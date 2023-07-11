from rest_framework.views import APIView, Response, Request, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Pet
from traits.models import Trait
from groups.models import Group
from .serializers import PetSerializer
from django.shortcuts import get_object_or_404


class PetsView(APIView, PageNumberPagination):
    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group_data = serializer.validated_data.pop("group")
        group_obj, created = Group.objects.get_or_create(
            scientific_name__iexact=group_data["scientific_name"],
            defaults={"scientific_name": group_data["scientific_name"]},
        )

        trait_data_list = serializer.validated_data.pop("traits", [])
        trait_obj_list = []
        for trait_data in trait_data_list:
            trait_obj, created = Trait.objects.get_or_create(
                name__iexact=trait_data["name"],
                defaults={"name": trait_data["name"]},
            )
            trait_obj_list.append(trait_obj)

        pet_obj = Pet.objects.create(
            group=group_obj,
            **serializer.validated_data,
        )
        pet_obj.traits.set(trait_obj_list)

        serializer = PetSerializer(pet_obj)
        return Response(serializer.data, status.HTTP_201_CREATED)

    def get(self, request: Request) -> Response:
        scientific_name = request.query_params.get("scientific_name", None)
        trait = request.query_params.get("trait", None)

        if scientific_name:
            scientific_name = scientific_name.lower()

        if trait:
            trait = trait.lower()

        if scientific_name and trait:
            pets = Pet.objects.filter(
                traits__name=trait, group__scientific_name=scientific_name
            )

        elif trait and not scientific_name:
            pets = Pet.objects.filter(traits__name=trait)

        elif scientific_name and not trait:
            pets = Pet.objects.filter(group__scientific_name=scientific_name)

        else:
            pets = Pet.objects.all()

        result_page = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        trait_data = serializer.validated_data.pop("traits", None)
        group_data = serializer.validated_data.pop("group", None)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        new_traits_list = []

        if trait_data:
            for trait in trait_data:
                trait_exist = Trait.objects.filter(name__icontains=trait["name"])

                trait_obj = (
                    trait_exist.first()
                    if trait_exist.exists()
                    else Trait.objects.create(name=trait["name"].lower())
                )

                new_traits_list.append(trait_obj)

            pet.traits.set(new_traits_list)

        if group_data:
            group_exist = Group.objects.filter(
                scientific_name__icontains=group_data["scientific_name"]
            )

            group_obj = (
                group_exist.first()
                if group_exist.exists()
                else Group.objects.create(
                    scientific_name=group_data["scientific_name"]
                )
            )

            pet.group = group_obj

        pet.save()

        serializer = PetSerializer(pet)

        return Response(serializer.data, status=status.HTTP_200_OK)
