frappe.ui.form.on("Task", {
    refresh(frm) {

        frm.add_custom_button("Create Task", () => {
            let d = new frappe.ui.Dialog({
                title: "Create Task",
                fields: [{label: "Task Subject",fieldname: "task_subject",fieldtype: "Data",}],

                primary_action_label: "Create Task",

                primary_action(values) {
                    frappe.call({
                        method: "clinic_management.clinic_management.api.create_task",
                        args: {
                            task_subject: values.task_subject
                        },
                        callback(r) {
                            d.hide();
                            frappe.msgprint(
                                "Task created successfully: " + r.message
                            );
                        }
                    });
                }
            });
            d.show();
        });
    }
});