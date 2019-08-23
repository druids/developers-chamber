from developers_chamber.django import get_project_info_dict


def get_project_info(request):
    return dict(('PROJECT_' + k.upper(), v) for k, v in get_project_info_dict().items())
