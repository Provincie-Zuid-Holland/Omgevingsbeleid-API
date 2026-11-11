from pydantic import BaseModel
from pydantic_core import ErrorDetails
from sqlalchemy.ext.asyncio import AsyncSession

from app.build.services.validators.types import ASYNC_VALIDATORS_ATTRIBUTE


class AsyncModelValidatorsService:
    async def run(
        self,
        session: AsyncSession,
        model: type[BaseModel],
        data: BaseModel,
        context: dict,
        loc: tuple = (),
    ) -> list[ErrorDetails]:
        """
        Runs the config-declared AsyncValidators on the model instance that pydantic already validated,
        and writes back values they changed. Errors use the pydantic error format.
        """
        errors: list[ErrorDetails] = []
        for field_name, validator in getattr(model, ASYNC_VALIDATORS_ATTRIBUTE, []):
            value = getattr(data, field_name, None)
            try:
                new_value = await validator.func(session, value, context)
            except ValueError as e:
                errors.append(
                    ErrorDetails(
                        type="value_error",
                        loc=(*loc, field_name),
                        msg=f"Value error, {e}",
                        input=value,
                    )
                )
                continue

            # Only write back changes: assigning marks the field as set, which model_dump(exclude_unset=True) would pick up
            if new_value is not value:
                setattr(data, field_name, new_value)

        # Static fields live in a nested model with validators of its own
        for field_name, field_info in model.model_fields.items():
            nested_model = field_info.annotation
            if isinstance(nested_model, type) and issubclass(nested_model, BaseModel):
                nested_data = getattr(data, field_name, None)
                if nested_data is not None:
                    errors += await self.run(session, nested_model, nested_data, context, (*loc, field_name))

        return errors
