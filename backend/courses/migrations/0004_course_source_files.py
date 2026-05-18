from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_unique_course_title_per_group'),
        ('groups', '0004_alter_group_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='source_files',
            field=models.ManyToManyField(
                blank=True,
                related_name='courses',
                to='groups.groupfile',
                verbose_name='Fichiers sources',
            ),
        ),
    ]
