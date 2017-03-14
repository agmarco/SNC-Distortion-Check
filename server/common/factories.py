import factory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.User"

    username = factory.Sequence("user{0}".format)
    password = "password"
    email = factory.LazyAttribute(lambda u: '{}@example.com'.format(u.username))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        '''
        Add groups to the user using:

            group = GroupFactory('admin')
            UserFactory(groups=[group])

        '''
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "auth.Group"

    name = factory.Sequence("group{0}".format)
