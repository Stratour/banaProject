document.addEventListener("DOMContentLoaded", function () {
    var videoContainer = document.getElementById('video-container');
    var video = document.getElementById('video-element');

    if (videoContainer && video) {
        videoContainer.addEventListener('click', function () {
            // Hide the thumbnail & play button
            this.classList.add('hidden');

            // Show and play the video
            video.classList.remove('hidden');
            video.play();
        });
    }
});