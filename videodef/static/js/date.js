document.querySelectorAll('.date').forEach(function(element) {
    flatpickr(element, {
        dateFormat: "d.m.Y",
        locale: "ru",
    });
});