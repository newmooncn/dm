openerp.winekar = function(instance) {
instance.web.UserMenu =  instance.web.Widget.extend({
    template: "UserMenu",
    init: function(parent) {
        this._super(parent);
        this.update_promise = $.Deferred().resolve();
    },
    start: function() {
        var self = this;
        this._super.apply(this, arguments);
        this.$el.on('click', '.oe_dropdown_menu li a[data-menu]', function(ev) {
            ev.preventDefault();
            var f = self['on_menu_' + $(this).data('menu')];
            if (f) {
                f($(this));
            }
        });
    },
    do_update: function () {
        var self = this;
        var fct = function() {
            var $avatar = self.$el.find('.oe_topbar_avatar');
            $avatar.attr('src', $avatar.data('default-src'));
            if (!self.session.uid)
                return;
            var func = new instance.web.Model("res.users").get_func("read");
            return self.alive(func(self.session.uid, ["name", "company_id"])).then(function(res) {
                var topbar_name = res.name;
                if(instance.session.debug)
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, instance.session.db);
                if(res.company_id[0] > 1)
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, res.company_id[1]);
                self.$el.find('.oe_topbar_name').text(topbar_name);
                if (!instance.session.debug) {
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, instance.session.db);
                }
                var avatar_src = self.session.url('/web/binary/image', {model:'res.users', field: 'image_small', id: self.session.uid});
                $avatar.attr('src', avatar_src);
            });
        };
        this.update_promise = this.update_promise.then(fct, fct);
    },
    on_menu_help: function() {
        window.open('http://www.dmems.com', '_blank');
    },
    on_menu_logout: function() {
        this.trigger('user_logout');
    },
    on_menu_settings: function() {
        var self = this;
        if (!this.getParent().has_uncommitted_changes()) {
            self.rpc("/web/action/load", { action_id: "base.action_res_users_my" }).done(function(result) {
                result.res_id = instance.session.uid;
                self.getParent().action_manager.do_action(result);
            });
        }
    },
    on_menu_about: function() {
        window.open("http://www.dmems.com","_blank");
    },
});
};