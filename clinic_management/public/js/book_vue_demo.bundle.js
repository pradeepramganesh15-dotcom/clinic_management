import { createApp } from 'vue';
import BookApp from './BookApp.vue';

frappe.ui.setup_vue = function (element) {
    const app = createApp(BookApp);
    app.mount(element.get(0));
    return app;
};