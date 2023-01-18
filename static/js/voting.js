$(document).on('click', '.accordion li', function(e) {
    $(this).find('div').slideToggle();
    $(this).find('svg').toggleClass('flipY');
});

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

