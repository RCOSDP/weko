from invenio_assets.webpack import WebpackThemeBundle

weko_workflow = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes = {
        "bootstrap3": dict(
            entry = {
                'workflow-detail': 'js/weko_workflow/workflow_detail.js',
                'workflow-item-link': 'js/weko_workflow/workflow_item_link.js',
                'activity-list': 'js/weko_workflow/activity_list.js',
                'bootstrap-datepicker': 'js/weko_workflow/bootstrap-datepicker.min.js',
                'iframe-pop':'js/weko_workflow/iframe_pop.js',
                'workflow-oa-policy':'js/weko_workflow/workflow_oa_policy.js',
                'workflow-identifier-grant':'js/weko_workflow/workflow_identifier_grant.js',
                'quit-confirmation':'js/weko_workflow/quit_confirmation.js',
                'lock-activity':'js/weko_workflow/lock_activity.js',
                'theme-flow-detail':'js/weko_workflow/admin/flow_detail.js',
                'theme-workflow':'css/weko_workflow/style.css',
                'theme-datepicker': 'css/weko_workflow/bootstrap-datepicker3.standalone.min.css',
            },
            dependencies={
                
            }
        )
    }
)