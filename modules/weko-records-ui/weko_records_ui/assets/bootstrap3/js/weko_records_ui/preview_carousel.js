import $ from 'jquery';

$(document).ready(function () {
    // Add indicators dynamically to avoid multiple looping
    function init_carousel() {
        $(document).find('.preview-carousel').each(function () {
            var carousel = $(this);
            var carouselItems = carousel.find('.carousel-inner').children('.item');
            var carouselId = carousel.attr('id');
            carouselItems.each(function (i) {
                if (carouselItems.length <= 1) { return false; }
                if (i == 0) {
                    carousel.find('.carousel-indicators')
                        .append('<li data-target="#' + carouselId + '" data-slide-to="' + i + '" class="active"></li>');
                }
                else {
                    carousel.find('.carousel-indicators')
                        .append('<li data-target="#' + carouselId + '" data-slide-to="' + i + '"></li>');
                }
            });
        });
    }

    // Open close preview manually -- support for multiple collapses
    $('.preview-panel-toggle').on('click', function () {
        var parentPanel = $(this).closest('.panel');
        if (parentPanel.find('.preview-panel-body').hasClass('hidden')) {
            $(this).find('.preview-arrow-right').addClass('hidden');
            parentPanel.find('.preview-panel-body').removeClass('hidden');
            $(this).find('.preview-arrow-down').removeClass('hidden');
        }
        else {
            parentPanel.find('.preview-panel-body').addClass('hidden');
            $(this).find('.preview-arrow-down').addClass('hidden');
            $(this).find('.preview-arrow-right').removeClass('hidden');
        }
    });

    // Start up carousel
    init_carousel();
});
