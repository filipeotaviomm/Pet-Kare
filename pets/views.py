from rest_framework.views import APIView, Response, Request, status
from pets.models import Pet
from pets.serializers import PetSerializer
from traits.models import Trait
from groups.models import Group
from rest_framework.pagination import PageNumberPagination


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        query_param = request.query_params.get("trait", None)
        if query_param:
            pets = Pet.objects.filter(traits__name__iexact=query_param)
        else:
            pets = Pet.objects.all()
        result_page = self.paginate_queryset(pets, request)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # essa linha de cima substitui as duas debaixo
        # if not serializer.is_valid():
        #     return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        group_data = serializer.validated_data.pop("group")
        traits_data = serializer.validated_data.pop("traits")

        try:
            group = Group.objects.get(
                **group_data
            )  # o de cima ou esse: scientific_name=group_data["scientific_name"]
        except Group.DoesNotExist:
            group = Group.objects.create(**group_data)

        pet = Pet.objects.create(**serializer.validated_data, group=group)

        for current_trait in traits_data:
            try:
                trait = Trait.objects.get(name__iexact=current_trait["name"])
            except Trait.DoesNotExist:
                trait = Trait.objects.create(**current_trait)

            pet.traits.add(trait)

        serializer = PetSerializer(pet)
        return Response(serializer.data, status.HTTP_201_CREATED)


class PetIdView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        try:
            found_pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found."}, status.HTTP_404_NOT_FOUND)
        serializer = PetSerializer(found_pet)
        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        try:
            found_pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found."}, status.HTTP_404_NOT_FOUND)

        found_pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request: Request, pet_id: int) -> Response:
        try:
            found_pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found."}, status.HTTP_404_NOT_FOUND)

        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        group_data = serializer.validated_data.pop("group", None)
        if group_data:
            try:
                group = Group.objects.get(**group_data)
            except Group.DoesNotExist:
                group = Group.objects.create(**group_data)
            found_pet.group = group

        traits_data = serializer.validated_data.pop("traits", None)
        if traits_data:
            new_traits = []
            for current_trait in traits_data:
                try:
                    trait = Trait.objects.get(name__iexact=current_trait["name"])
                except Trait.DoesNotExist:
                    trait = Trait.objects.create(**current_trait)
                new_traits.append(trait)
            found_pet.traits.set(new_traits)

        for key, value in serializer.validated_data.items():
            setattr(found_pet, key, value)
        found_pet.save()
        serializer = PetSerializer(found_pet)

        return Response(serializer.data, status.HTTP_200_OK)
