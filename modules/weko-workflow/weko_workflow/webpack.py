from invenio_assets.webpack import WebpackThemeBundle

weko_workflow = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                'workflow-js-workflow': './js/weko_workflow/workflow_detail.js',
                'workflow-js-item-link': './js/weko_workflow/workflow_item_link.js',
                'workflow-js-activity-list': './js/weko_workflow/js_activity_list.js',
                'workflow-js-iframe': './js/weko_workflow/iframe_pop.js',
                'workflow-js-oa-policy': './js/weko_workflow/workflow_oa_policy.js',
                'workflow-js-identifier-grant': './js/weko_workflow/workflow_identifier_grant.js',
                'workflow-js-quit-confirmation': './js/weko_workflow/quit_confirmation.js',
                'workflow-js-lock-activity': './js/weko_workflow/lock_activity.js',
                'workflow-js-admin-workflow-detail': './js/weko_workflow/admin/workflow_detail.js',
                'workflow-css-workflow': './css/weko_workflow/style.css',
                'workflow-css-datepicker-workflow': './css/weko_workflow/bootstrap-datepicker3.standalone.min.css',
                'workflow-js-admin-flow-detail': './js/weko_workflow/admin/flow_detail.js',
                },
            dependencies={
                
            }
        )
    }
)