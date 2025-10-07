// Get the modal
var loginModal = document.getElementById('loginModal');
var registerModal = document.getElementById('registerModal');

// Get the buttons that open the modals
var loginBtn = document.getElementById('loginBtn');
var registerBtn = document.getElementById('registerBtn');

// Get the <span> elements that close the modals
var spans = document.getElementsByClassName('close');

// When the user clicks the button, open the modals
loginBtn.onclick = function() {
  loginModal.style.display = 'block';
}

registerBtn.onclick = function() {
  registerModal.style.display = 'block';
}

// When the user clicks on <span> (x), close the modals
for (var i = 0; i < spans.length; i++) {
  spans[i].onclick = function() {
    loginModal.style.display = 'none';
    registerModal.style.display = 'none';
  }
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == loginModal) {
    loginModal.style.display = 'none';
  } else if (event.target == registerModal) {
    registerModal.style.display = 'none';
  }
}