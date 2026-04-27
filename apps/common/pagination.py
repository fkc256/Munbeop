from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """프로젝트 공용 페이지네이션.

    - ``?page_size=`` 로 클라이언트가 페이지 크기 조절 가능.
    - ``max_page_size`` 초과 요청은 자동으로 상한값으로 잘림 (DoS 방지).
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"
