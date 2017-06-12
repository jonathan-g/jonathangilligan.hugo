"use strict";

jQuery(function() {

    /**
     * show-all function for fade-in all not visible category items
     */
    jQuery(".category_showall").click(function() {
        jQuery(".item_category").parent().fadeIn("slow", function() {});
    });

    /**
     * hide function for all categories
     */
    jQuery(".item_category").click(function() {
        jQuery("[data-category=" + jQuery(this).attr("data-category") + "]").parent().fadeOut("slow", function() {});
    });


    /**
     * generate toc if exists
     */
    jQuery("#toc").toc({
        "selectors": "h2,h3,h4,h5,h6",
        "container": ".body"
    });

    /**
     * hide / show toc button
     */
    jQuery("#tochideshow").click(function() {
        jQuery("#toc").fadeToggle("slow", function() {
            jQuery("#tochideshow").text().match(/hide/i) ? jQuery("#tochideshow").text("Show") : jQuery("#tochideshow").text("Hide");
        });
    });


    /**
     * navigation for small windows
     */
    jQuery("#nav").click(function() {
        if (!jQuery(".sidebar").data("active")) {
            jQuery(".sidebar").css("width", "250px");
            jQuery(".sidebar").css("margin-left", "0");
            jQuery(".sidebar").data("active", true);
        } else {
            jQuery(".sidebar").css("width", "0");
            jQuery(".sidebar").css("margin-left", "0");
            jQuery(".sidebar").data("active", false);
        }
    });


    /**
     * teletyping initialization
     */
    jQuery(".teletype").each(function() {

        jQuery(this).teletype({
            text: jQuery(this).find("p.command").map(function() {
                return jQuery(this).text().trim();
            }),
            result: jQuery(this).find("p.result").map(function() {
                return jQuery(this).html();
            }),
            prefix: jQuery(this).attr("data-prefix"),
            cursor: "\u258B",
            automaticstart: false
        });

    });

    /**
     * rest teletyping element
     */
    jQuery(".teletypereset").click(function() {
        jQuery("#" + jQuery(this).attr("data-terminal")).teletype().reset().start();
    });


    /**
     * add anchor on headlines
     */
    jQuery("h2,h3,h4,h5,h6").filter("[id]").each(function () {
        jQuery(this).html( "<a href=\"#" + jQuery(this).attr("id") + "\">" + jQuery(this).html() + "</a>" );
    });


    /**
     * tooltip toggle
     */
    jQuery(".tooltiptoggle").click( function() { 
        jQuery(this).children(".tooltipcontent:first").slideToggle(); 
    });


    /**
     * swipe-left to go to the next page
     */
    jQuery("body").hammer().bind("swipeleft", function(){
        var lc = jQuery(this).data("nextpage");
        if (lc)
            window.location.href = lc;
    });

    /**
     * swipe-right to got to the previous page
     */
    jQuery("body").hammer().bind("swiperight", function(){
        var lc = jQuery(this).data("previouspage");
        if (lc)
            window.location.href = lc;
    });

});
