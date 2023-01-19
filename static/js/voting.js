
// Handle animation in on the vote and submit functionality widget
$(document).on('click', '.arrow-button', function(e) {

    console.log("got here")

    $(this).parent().parent().parent().find('.feature-description').slideToggle();
    $(this).parent().parent().parent().find('.arrow-button').toggleClass('flipY');
});

// Handle tab switching in on the vote and submit functionality widget
$(document).ready(function() {
    $(".vote-func-tab").click(function() {
      $(".submit-func").hide();
      $(".vote-func").show();
    });
    
    $(".submit-func-tab").click(function() {
      $(".vote-func").hide();
      $(".submit-func").show();
    });
  });