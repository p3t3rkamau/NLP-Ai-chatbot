document.getElementsByClassName('clear-btn')[0].addEventListener('click', function() {
    document.cookie = "conversation_history=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    localStorage.removeItem('chatHistory');
    location.reload();
});

(function($) { // Begin jQuery
    $(function() { // DOM ready
      // If a link has a dropdown, add sub menu toggle.
      $('nav ul li a:not(:only-child)').click(function(e) {
        $(this).siblings('.nav-dropdown').toggle();
        // Close one dropdown when selecting another
        $('.nav-dropdown').not($(this).siblings()).hide();
        e.stopPropagation();
      });
      // Clicking away from dropdown will remove the dropdown class
      $('html').click(function() {
        $('.nav-dropdown').hide();
      });
      // Toggle open and close nav styles on click
      $('#nav-toggle').click(function() {
        $('nav ul').slideToggle();
      });
      // Hamburger to X toggle
      $('#nav-toggle').on('click', function() {
        this.classList.toggle('active');
      });
    }); // end DOM ready
  })(jQuery); // end jQuery

chatcontainer = document.querySelector('.chat-container')
chatLink = document.querySelector('.chatLink')  
chatLink.addEventListener('click', function(){
    chatcontainer.style.display = 'none'
})


document.getElementsByClassName("chatLink").addEventListener("click", function() {
    document.getElementsByClassName("chat-container").style.display = "block";
});

