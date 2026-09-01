frappe.pages["book_vue_demo"].on_page_load = function (wrapper) {

    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Book Dashboard (Vue)",
        single_column: true
    });

    let $root = $('<div id="vue-book-root" style="padding: 15px;"></div>')
        .appendTo(page.main);

    function renderApp() {
        if (window.frappe && frappe.ui && frappe.ui.setup_vue) {
            frappe.ui.setup_vue($root);
        } else {
            setTimeout(renderApp, 200);
        }
    }

    // Vue bundle
    frappe.require("book_vue_demo.bundle.js").then(() => {
        renderApp();
    });

    // Asset bundle
    frappe.require("asset_demo.bundle.js").then(() => {
        console.log("Asset bundle loaded successfully!");
    });

};