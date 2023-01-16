$(document).on('click', '.accordion li', function(e) {
    $(this).find('div').slideToggle();
    $(this).find('svg').toggleClass('flipY');
});

$(document).on('click', '.tab-form', function(e) {
    $(this).toggleClass('hidden-form');
});