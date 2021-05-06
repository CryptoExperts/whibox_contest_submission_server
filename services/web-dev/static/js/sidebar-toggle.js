$(function() {
    $(document).ready(function () {
        var toggled = Cookies.get("sidebar-toggled");
        if (toggled == "true") {
             $("#accordionSidebar").addClass('toggled');
        } else {
             $("#accordionSidebar").removeClass('toggled');
        }

        $('#sidebarToggle').on('click', function () {
            let toggled = ($('#accordionSidebar').hasClass('toggled')) ? true : false;
            Cookies.set("sidebar-toggled", toggled);
        });
    });

});
