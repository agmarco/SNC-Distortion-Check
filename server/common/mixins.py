from django.http import HttpResponseRedirect


class DeletionMixin(object):
    """A mixin providing the ability to delete objects by setting their 'deleted' attribute."""

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())
