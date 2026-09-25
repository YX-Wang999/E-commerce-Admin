"""Customer-facing API exceptions."""

from rest_framework.exceptions import APIException

from common.codes import LOGIN_REQUIRED


class CustomerLoginRequired(APIException):
    """B 类接口未登录：返回 code 10001，供前端弹出登录框。"""

    status_code = 401
    default_detail = '请先登录'
    default_code = LOGIN_REQUIRED
