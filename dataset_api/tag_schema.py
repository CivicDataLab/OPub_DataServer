import graphene
from graphene_django import DjangoObjectType

from .models import Organization, Tag


class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = "__all__"


class Query(graphene.ObjectType):
    all_tag = graphene.List(TagType)
    tag = graphene.Field(TagType, tag_id=graphene.Int())

    def resolve_all_tag(self, info, **kwargs):
        return Tag.objects.all()

    def resolve_tag(self, info, tag_id):
        return Tag.objects.get(pk=tag_id)


class TagInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    # organization = graphene.String()


class CreateTag(graphene.Mutation):
    class Arguments:
        tag_data = TagInput(required=True)

    tag = graphene.Field(TagType)

    @staticmethod
    def mutate(root, info, tag_data=None):
        # organization = Organization.objects.get(id=tag_data.organization)
        tag_instance = Tag(
            name=tag_data.name,
        )
        tag_instance.save()
        return CreateTag(tag=tag_instance)


class Mutation(graphene.ObjectType):
    create_tag = CreateTag.Field()
