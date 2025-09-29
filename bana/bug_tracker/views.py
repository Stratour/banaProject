from django.shortcuts import render

#def bug_tracker(request):
#    pass


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from .models import Bug, BugComment, BugAttachment, BugHistory, Component, Version, Environment
from .forms import BugForm, BugCommentForm, BugFilterForm, BugAttachmentForm
import json

@login_required
def bug_list(request):
    bugs = Bug.objects.select_related(
        'component', 'assigned_to', 'reported_by', 'affected_version', 'environment'
    ).all()
    
    # Filtrage
    form = BugFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['status']:
            bugs = bugs.filter(status=form.cleaned_data['status'])
        if form.cleaned_data['priority']:
            bugs = bugs.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data['component']:
            bugs = bugs.filter(component=form.cleaned_data['component'])
        if form.cleaned_data['assigned_to']:
            bugs = bugs.filter(assigned_to=form.cleaned_data['assigned_to'])
        if form.cleaned_data['search']:
            search = form.cleaned_data['search']
            bugs = bugs.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(bugs, 20)
    page = request.GET.get('page', 1)
    bugs_page = paginator.get_page(page)
    
    # Si c'est une requête HTMX, on retourne seulement la table
    if request.htmx:
        return render(request, 'bug_tracker/partials/bug_table.html', {
            'bugs': bugs_page,
            'form': form
        })
    
    return render(request, 'bug_tracker/bug_list.html', {
        'bugs': bugs_page,
        'form': form
    })

@login_required
def bug_detail(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    comments = bug.comments.select_related('author').all()
    attachments = bug.attachments.select_related('uploaded_by').all()
    history = bug.history.select_related('user').all()[:10]  # 10 dernières modifications
    
    return render(request, 'bug_tracker/bug_detail.html', {
        'bug': bug,
        'comments': comments,
        'attachments': attachments,
        'history': history,
        'comment_form': BugCommentForm()
    })

@login_required
def bug_create(request):
    if request.method == 'POST':
        form = BugForm(request.POST)
        if form.is_valid():
            bug = form.save(commit=False)
            bug.reported_by = request.user
            bug.save()
            
            # Créer l'historique
            BugHistory.objects.create(
                bug=bug,
                user=request.user,
                field_changed='created',
                new_value='Bug créé'
            )
            
            messages.success(request, f'Bug #{bug.id} créé avec succès!')
            
            if request.htmx:
                return HttpResponse(headers={'HX-Redirect': bug.get_absolute_url()})
            return redirect(bug.get_absolute_url())
    else:
        form = BugForm()
    
    if request.htmx:
        return render(request, 'bug_tracker/partials/bug_form.html', {'form': form})
    
    return render(request, 'bug_tracker/bug_create.html', {'form': form})

@login_required
def bug_edit(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    old_values = {}
    
    if request.method == 'POST':
        # Sauvegarder les anciennes valeurs pour l'historique
        for field in ['status', 'priority', 'severity', 'assigned_to', 'component']:
            old_values[field] = str(getattr(bug, field))
        
        form = BugForm(request.POST, instance=bug)
        if form.is_valid():
            updated_bug = form.save()
            
            # Créer l'historique des modifications
            for field in ['status', 'priority', 'severity', 'assigned_to', 'component']:
                new_value = str(getattr(updated_bug, field))
                if old_values[field] != new_value:
                    BugHistory.objects.create(
                        bug=updated_bug,
                        user=request.user,
                        field_changed=field,
                        old_value=old_values[field],
                        new_value=new_value
                    )
            
            messages.success(request, f'Bug #{bug.id} mis à jour!')
            
            if request.htmx:
                return render(request, 'bug_tracker/partials/bug_detail_content.html', {
                    'bug': updated_bug
                })
            return redirect(bug.get_absolute_url())
    else:
        form = BugForm(instance=bug)
    
    if request.htmx:
        return render(request, 'bug_tracker/partials/bug_edit_form.html', {
            'form': form, 
            'bug': bug
        })
    
    return render(request, 'bug_tracker/bug_edit.html', {'form': form, 'bug': bug})

@login_required
@require_POST
def bug_status_update(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(Bug.STATUS_CHOICES):
        old_status = bug.status
        bug.status = new_status
        bug.save()
        
        # Créer l'historique
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            field_changed='status',
            old_value=old_status,
            new_value=new_status
        )
        
        if request.htmx:
            return render(request, 'bug_tracker/partials/bug_status_badge.html', {
                'bug': bug
            })
    
    return JsonResponse({'success': False})

@login_required
@require_POST
def add_comment(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    form = BugCommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.bug = bug
        comment.author = request.user
        comment.save()
        
        # Créer l'historique
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            field_changed='comment_added',
            new_value=f'Commentaire ajouté: {comment.content[:50]}...'
        )
        
        if request.htmx:
            comments = bug.comments.select_related('author').all()
            return render(request, 'bug_tracker/partials/comments_section.html', {
                'bug': bug,
                'comments': comments,
                'comment_form': BugCommentForm()
            })
    
    return JsonResponse({'success': False})

@login_required
@require_POST
def upload_attachment(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    form = BugAttachmentForm(request.POST, request.FILES)
    
    if form.is_valid():
        attachment = form.save(commit=False)
        attachment.bug = bug
        attachment.uploaded_by = request.user
        attachment.filename = attachment.file.name
        attachment.save()
        
        # Créer l'historique
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            field_changed='attachment_added',
            new_value=f'Fichier ajouté: {attachment.filename}'
        )
        
        if request.htmx:
            attachments = bug.attachments.select_related('uploaded_by').all()
            return render(request, 'bug_tracker/partials/attachments_section.html', {
                'bug': bug,
                'attachments': attachments
            })
    
    return JsonResponse({'success': False})

@login_required
def bug_assign(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    
    if request.method == 'POST':
        user_id = request.POST.get('assigned_to')
        old_assignee = bug.assigned_to
        
        if user_id:
            from django.contrib.auth.models import User
            try:
                new_assignee = User.objects.get(pk=user_id)
                bug.assigned_to = new_assignee
            except User.DoesNotExist:
                bug.assigned_to = None
        else:
            bug.assigned_to = None
        
        bug.save()
        
        # Créer l'historique
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            field_changed='assigned_to',
            old_value=str(old_assignee) if old_assignee else 'Non assigné',
            new_value=str(bug.assigned_to) if bug.assigned_to else 'Non assigné'
        )
        
        if request.htmx:
            return render(request, 'bug_tracker/partials/bug_assignee.html', {'bug': bug})
    
    return JsonResponse({'success': False})

def bug_stats(request):
    """Statistiques pour le dashboard"""
    from django.db.models import Count
    
    stats = {
        'total': Bug.objects.count(),
        'open': Bug.objects.filter(status='open').count(),
        'in_progress': Bug.objects.filter(status='in_progress').count(),
        'resolved': Bug.objects.filter(status='resolved').count(),
        'by_priority': dict(Bug.objects.values('priority').annotate(count=Count('id'))),
        'by_component': dict(Bug.objects.values('component__name').annotate(count=Count('id')))
    }
    
    if request.htmx:
        return render(request, 'bug_tracker/partials/dashboard_stats.html', {'stats': stats})
    
    return render(request, 'bug_tracker/dashboard.html', {'stats': stats})
