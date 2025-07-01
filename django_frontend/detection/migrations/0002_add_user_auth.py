# Generated migration for user authentication

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('detection', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='detectionrecord',
            name='user',
            field=models.ForeignKey(
                default=1,
                help_text='检测记录所属用户',
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name='用户'
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('last_login_ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='最后登录IP')),
                ('login_count', models.IntegerField(default=0, verbose_name='登录次数')),
                ('is_locked', models.BooleanField(default=False, verbose_name='账户是否锁定')),
                ('locked_until', models.DateTimeField(blank=True, null=True, verbose_name='锁定到期时间')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户配置',
                'verbose_name_plural': '用户配置',
                'ordering': ['-created_time'],
            },
        ),
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=150, verbose_name='用户名')),
                ('ip_address', models.GenericIPAddressField(verbose_name='IP地址')),
                ('success', models.BooleanField(default=False, verbose_name='是否成功')),
                ('attempt_time', models.DateTimeField(auto_now_add=True, verbose_name='尝试时间')),
                ('user_agent', models.TextField(blank=True, verbose_name='用户代理')),
            ],
            options={
                'verbose_name': '登录尝试',
                'verbose_name_plural': '登录尝试',
                'ordering': ['-attempt_time'],
            },
        ),
        migrations.AddIndex(
            model_name='loginattempt',
            index=models.Index(fields=['username', 'ip_address', 'attempt_time'], name='detection_l_usernam_b8e5a5_idx'),
        ),
        migrations.AddIndex(
            model_name='loginattempt',
            index=models.Index(fields=['success', 'attempt_time'], name='detection_l_success_8b7c8a_idx'),
        ),
    ]
