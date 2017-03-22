from django.http import HttpResponseRedirect


class DeletionMixin(object):
    """A mixin providing the ability to delete objects by setting their 'deleted' attribute."""

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(success_url)
