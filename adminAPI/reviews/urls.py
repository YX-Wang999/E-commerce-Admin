"""Review URL routes."""

from django.urls import path

from reviews.views import (
    ProductReviewListView,
    ProductReviewSubmitView,
    ReviewCommentCreateView,
    ReviewCommentListView,
    ReviewCreateView,
    ReviewDetailView,
    ReviewFollowUpView,
    ReviewLikeView,
    ReviewUserCenterView,
    ReviewViewIncrementView,
)

urlpatterns = [
    path('', ReviewCreateView.as_view(), name='review-create'),
    path('user/', ReviewUserCenterView.as_view(), name='review-user-center'),
    path('product/<int:product_id>/', ProductReviewListView.as_view(), name='review-product-list'),
    path('<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('<int:pk>/like/', ReviewLikeView.as_view(), name='review-like'),
    path('<int:pk>/comment/', ReviewCommentCreateView.as_view(), name='review-comment-create'),
    path('<int:pk>/comments/', ReviewCommentListView.as_view(), name='review-comment-list'),
    path('<int:pk>/view/', ReviewViewIncrementView.as_view(), name='review-view'),
    path('<int:pk>/follow-up/', ReviewFollowUpView.as_view(), name='review-follow-up'),
    path('submit/', ProductReviewSubmitView.as_view(), name='review-submit-legacy'),
]
