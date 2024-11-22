import asyncio
from typing import Any
from prisma import Prisma
from prisma.models import Doctor, Patient, SoapNote
from datetime import datetime
import json


class VMMService:
    def __init__(self) -> None:
        self.prisma = Prisma()

    async def connect(self) -> None:
        await self.prisma.connect()

    async def disconnect(self) -> None:
        await self.prisma.disconnect()

    def get_model(self, model: str) -> type[Any] | None:
        try:
            target_attribute = getattr(self.prisma, model.lower())
            return target_attribute
        except AttributeError as e:
            print(f"Model '{model}' not found on 'self.prisma'.")
            return None

    async def add_doctor(self, name: str) -> Doctor:
        new_doctor: Doctor = await self.prisma.doctor.create(
            data={
                "name": name,
            }
        )

        return new_doctor
        

    async def add_patient(
        self,
        doctor: Doctor,
        name: str,
        sex: str,
        dob: datetime | None = None,
    ) -> Patient:
        new_patient = await self.prisma.patient.create(
            data={
                "name": name,
                "dob": dob.astimezone().isoformat() if dob else None,
                "sex": sex,
                "doctor": {
                    "connect": {"id": doctor.id},
                },
            },
        )

        return new_patient

    async def add_soapnote(
        self, patient: Patient, note_content: Any | None = None
    ) -> SoapNote:
        json_note_content = json.dumps(note_content)

        new_soapnote: SoapNote = await self.prisma.soapnote.create(
            data={
                "noteContent": json_note_content,
                "patient": {
                    "connect": {"id": patient.id},
                },
            }
        )

        return new_soapnote

    async def update_soapnote(
        self, soapnote_entry_id: str, note_content: Any | None
    ) -> None:
        json_note_content = json.dumps(note_content)

        await self.prisma.soapnote.update(
            where={"id": soapnote_entry_id},
            data={"noteContent": json_note_content},
        )

    async def list_doctor_patients(self, doctor: Doctor) -> list[Patient]:
        query_result: list[Patient] = await self.prisma.patient.find_many(
            where={
                "doctorId": doctor.id,
            }
        )

        return query_result
    
    async def find_doctor_by_name(self, name: str):
        # Use Prisma's findUnique method to search by the 'name' field
        query_result = await self.prisma.doctor.find_unique(
           where={
               "name": name,  # Search by the 'name' field in the Doctor model
           }
        )
        return query_result



    async def search_unique(self, model: str, **kwargs: dict[str, Any]) -> Any | None:
        query_result: Any = await self.get_model(model).find_unique(
            where=kwargs,
        )

        return query_result

    async def search_many(
        self, model: str, **kwargs: dict[str, Any]
    ) -> list[Any] | None:
        query_result: list[Any] = await self.get_model(model).find_many(
            where=kwargs,
        )

        return query_result

    async def search_name(self, model: str, name: str) -> Any | None:
        query_result: list[Any] = await self.get_model(model).find_many(
            where={
                "name": {
                    "contains": name,
                    "mode": "insensitive",
                },
            }
        )

        return query_result

    async def list_all(self, model: str) -> list[Any] | None:
        query_result: list[Any] = await self.get_model(model).find_many()
        return query_result

    async def remove_all(self, model: str) -> None:
        await self.get_model(model).delete_many()
    
    async def remove_patient(self, patient_id: str) -> None:
        patient_model = (self.get_model("Patient"))
        print("removing patient id: "  + patient_id)
        await patient_model.delete_many({"id": patient_id})

    async def add_appointment(self, doctor_id: str, patient_id: str, title: str, start, end):
        return await self.prisma.appointments.create(
            data={
                "doctorId": doctor_id,
                "patientId": patient_id,
                "content": title,
                "start": start,
                "end": end,
            }
        )
    
    async def get_events_by_doctor_id(self, doctor_id: str) -> list[dict]:
        appointments = await self.prisma.appointments.find_many(where={"doctorId": doctor_id})
        return await self.appointments_to_dict(appointments)

    async def appointments_to_dict(self, appointments: list) -> list[dict]:
        return [
            {
                "id": appointment.id,
                "doctorId": appointment.doctorId,
                "patientId": appointment.patientId,
                "content": appointment.content,
                "start": appointment.start.isoformat(),
                "end": appointment.end.isoformat(),
            }
            for appointment in appointments
        ]



async def cleanup(client):
    await client.remove_all("doctor")
    await client.remove_all("patient")
    await client.remove_all("appointments")

    # All new records
    new_doc = await client.add_doctor("John Doe")

    new_patient = await client.add_patient(
        new_doc, "Meow", "Male", datetime(2001, 5, 24)
    )

    print(new_doc)
    print()
    print(new_patient)
    print()

    # List all patients assigned to new_doc

    new_soap_note = await client.add_soapnote(
        new_patient, {"skibidi": "sigma", "alpha": "wolf"}
    )

    print(new_soap_note)

    print(new_patient)

async def main() -> None:

    client = VMMService()

    await client.connect()

    try:
        # Check if the "Doctor" table exists by attempting a query
        doctor_count = await client.doctor.count()
        
        if doctor_count == 0:
            print("No doctors found in the database. Performing cleanup...")
            await cleanup(client)
        else:
            print(f"Found {doctor_count} doctor(s). No cleanup needed.")
            
    except Exception:
        # If the table does not exist, handle this situation gracefully
        print("Doctor table does not exist. Performing cleanup...")
        await cleanup(client)
    finally:
        # Disconnect the Prisma client
        await client.disconnect()

    

if __name__ == "__main__":
    asyncio.run(main())
