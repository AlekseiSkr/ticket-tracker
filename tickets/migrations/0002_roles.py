"""Role groups. The app checks permissions, never group names; the groups only bundle them."""

from django.contrib.auth.management import create_permissions
from django.db import migrations

LEAD = "Support Lead"
AGENT = "Agent"

ROLE_PERMISSIONS = {
    LEAD: [
        "tickets.view_all_tickets",
        "tickets.assign_ticket",
        "tickets.close_ticket",
        "tickets.change_priority",
        *[f"tickets.{verb}_{model}" for verb in ("view", "add", "change") for model in ("ticket", "comment")],
        *[f"tickets.{verb}_{model}" for verb in ("view", "add", "change", "delete") for model in ("customer", "agent", "tag")],
        *[f"auth.{verb}_{model}" for verb in ("view", "add", "change") for model in ("user", "group")],
    ],
    # No delete anywhere, nothing on agents (their WIP caps stay hidden), users or groups.
    AGENT: [
        "tickets.view_ticket",
        "tickets.add_ticket",
        "tickets.change_ticket",
        "tickets.view_comment",
        "tickets.add_comment",
        "tickets.view_customer",
        "tickets.add_customer",
        "tickets.change_customer",
        "tickets.view_tag",
    ],
}


def create_roles(apps, schema_editor):
    # Permissions are normally created after migrate; the groups need them now.
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for name, perms in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=name)
        objs = []
        for perm in perms:
            app_label, codename = perm.split(".")
            objs.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
        group.permissions.set(objs)


def delete_roles(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name__in=ROLE_PERMISSIONS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(create_roles, delete_roles)]
