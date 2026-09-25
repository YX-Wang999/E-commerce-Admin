"""RBAC models."""

from django.db import models


class Permission(models.Model):
    """API permission definition."""

    name = models.CharField(max_length=64, verbose_name='权限名称')
    code = models.CharField(max_length=128, unique=True, verbose_name='权限编码')
    module = models.CharField(max_length=64, verbose_name='所属模块')
    action = models.CharField(max_length=32, verbose_name='操作类型')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'rbac_permission'
        verbose_name = '权限'
        verbose_name_plural = verbose_name
        ordering = ['module', 'code']

    def __str__(self) -> str:
        return self.name


class Role(models.Model):
    """Role groups permissions and menus."""

    name = models.CharField(max_length=64, verbose_name='角色名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='角色编码')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        verbose_name='权限',
    )
    menus = models.ManyToManyField(
        'Menu',
        blank=True,
        related_name='roles',
        verbose_name='菜单',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'rbac_role'
        verbose_name = '角色'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self) -> str:
        return self.name


class Menu(models.Model):
    """Sidebar menu tree."""

    MENU_TYPE_DIRECTORY = 'directory'
    MENU_TYPE_MENU = 'menu'
    MENU_TYPE_BUTTON = 'button'
    MENU_TYPE_CHOICES = [
        (MENU_TYPE_DIRECTORY, '目录'),
        (MENU_TYPE_MENU, '菜单'),
        (MENU_TYPE_BUTTON, '按钮'),
    ]

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='父级菜单',
    )
    title = models.CharField(max_length=64, verbose_name='菜单标题')
    name = models.CharField(max_length=64, blank=True, default='', verbose_name='路由名称')
    path = models.CharField(max_length=255, blank=True, default='', verbose_name='路由路径')
    component = models.CharField(max_length=255, blank=True, default='', verbose_name='组件路径')
    icon = models.CharField(max_length=64, blank=True, default='', verbose_name='图标')
    menu_type = models.CharField(
        max_length=16,
        choices=MENU_TYPE_CHOICES,
        default=MENU_TYPE_MENU,
        verbose_name='菜单类型',
    )
    permission = models.ForeignKey(
        Permission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='menus',
        verbose_name='关联权限',
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_visible = models.BooleanField(default=True, verbose_name='是否可见')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'rbac_menu'
        verbose_name = '菜单'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.title
