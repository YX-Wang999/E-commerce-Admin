# Generated manually for review social features

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0009_tenant_description'),
        ('reviews', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productreview',
            name='allow_comment',
            field=models.BooleanField(default=True, verbose_name='允许评论'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='comment_count',
            field=models.PositiveIntegerField(default=0, verbose_name='评论数'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='follow_up_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='追评时间'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='follow_up_content',
            field=models.TextField(blank=True, default='', verbose_name='追评内容'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='follow_up_images',
            field=models.JSONField(blank=True, default=list, verbose_name='追评图片'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='follow_up_video',
            field=models.URLField(blank=True, default='', verbose_name='追评视频'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='images',
            field=models.JSONField(blank=True, default=list, verbose_name='图片'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='is_anonymous',
            field=models.BooleanField(default=False, verbose_name='匿名'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='is_public',
            field=models.BooleanField(default=True, verbose_name='公开'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='like_count',
            field=models.PositiveIntegerField(default=0, verbose_name='点赞数'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='status',
            field=models.CharField(
                choices=[('published', '已发布'), ('hidden', '已隐藏'), ('deleted', '已删除')],
                db_index=True,
                default='published',
                max_length=16,
                verbose_name='状态',
            ),
        ),
        migrations.AddField(
            model_name='productreview',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='product_reviews',
                to='tenants.tenant',
                verbose_name='商家',
            ),
        ),
        migrations.AddField(
            model_name='productreview',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新时间'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='video',
            field=models.URLField(blank=True, default='', verbose_name='视频'),
        ),
        migrations.AddField(
            model_name='productreview',
            name='view_count',
            field=models.PositiveIntegerField(default=0, verbose_name='浏览数'),
        ),
        migrations.CreateModel(
            name='ReviewComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=500, verbose_name='评论内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_comments', to='customers.customer', verbose_name='会员')),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='reviews.productreview', verbose_name='评价')),
            ],
            options={
                'verbose_name': '评价评论',
                'verbose_name_plural': '评价评论',
                'db_table': 'review_comment',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ReviewLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_likes', to='customers.customer', verbose_name='会员')),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='reviews.productreview', verbose_name='评价')),
            ],
            options={
                'verbose_name': '评价点赞',
                'verbose_name_plural': '评价评价点赞',
                'db_table': 'review_like',
                'unique_together': {('review', 'customer')},
            },
        ),
        migrations.AddConstraint(
            model_name='productreview',
            constraint=models.UniqueConstraint(
                condition=models.Q(('order__isnull', False)),
                fields=('customer', 'product', 'order'),
                name='uniq_review_customer_product_order',
            ),
        ),
    ]
