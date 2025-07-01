"""
设置用户认证系统的管理命令
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from detection.models import UserProfile, DetectionRecord


class Command(BaseCommand):
    help = '设置用户认证系统，创建默认管理员用户并迁移现有数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='管理员用户名（默认：admin）'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='管理员密码（默认：admin123）'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='管理员邮箱（默认：admin@example.com）'
        )
        parser.add_argument(
            '--skip-migration',
            action='store_true',
            help='跳过数据迁移'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        skip_migration = options['skip_migration']

        self.stdout.write(
            self.style.SUCCESS('开始设置用户认证系统...')
        )

        try:
            with transaction.atomic():
                # 1. 创建或更新管理员用户
                admin_user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                    }
                )
                
                if created:
                    admin_user.set_password(password)
                    admin_user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 创建管理员用户: {username}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'管理员用户 {username} 已存在')
                    )

                # 2. 创建用户配置
                profile, created = UserProfile.objects.get_or_create(
                    user=admin_user,
                    defaults={
                        'login_count': 0,
                        'is_locked': False,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 创建用户配置: {username}')
                    )

                # 3. 迁移现有检测记录（如果需要）
                if not skip_migration:
                    self.migrate_existing_records(admin_user)

                self.stdout.write(
                    self.style.SUCCESS('\n用户认证系统设置完成！')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'管理员账户: {username}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'管理员密码: {password}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'管理员邮箱: {email}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'设置失败: {str(e)}')
            )
            raise

    def migrate_existing_records(self, admin_user):
        """迁移现有的检测记录到管理员用户"""
        try:
            # 查找没有关联用户的检测记录
            orphan_records = DetectionRecord.objects.filter(user__isnull=True)
            count = orphan_records.count()
            
            if count > 0:
                # 将这些记录关联到管理员用户
                orphan_records.update(user=admin_user)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 迁移 {count} 条检测记录到管理员用户')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✓ 没有需要迁移的检测记录')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'数据迁移失败: {str(e)}')
            )

    def create_test_users(self):
        """创建测试用户（可选）"""
        test_users = [
            {'username': 'testuser1', 'password': 'test123', 'email': 'test1@example.com'},
            {'username': 'testuser2', 'password': 'test123', 'email': 'test2@example.com'},
        ]
        
        for user_data in test_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                
                # 创建用户配置
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'login_count': 0,
                        'is_locked': False,
                    }
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 创建测试用户: {user_data["username"]}')
                )
