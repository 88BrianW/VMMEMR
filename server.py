from quart import Quart, request, render_template, jsonify, redirect, url_for
from markupsafe import Markup
import utils
from database import VMMService
from datetime import datetime
import json
import os

app = Quart(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)

db = VMMService()


@app.template_global("get_year")
def get_year():
    return datetime.today().year


@app.before_serving
async def startup():
    await db.connect()


@app.after_serving
async def shutdown():
    await db.disconnect()


@app.route("/")
async def index():
    return await render_template("index.html")




@app.route("/soap-notes/<uuid:soapnote_id>", methods=["GET", "POST"])
async def soap_notes(soapnote_id):
    soapnote_helper = utils.SoapNoteTemplate(db, str(soapnote_id))

    if request.method == "POST":
        form_data = await request.form
        await soapnote_helper.update_soapnote_content(form_data)

        return "OK"
    
    else:
        form_html = await soapnote_helper.get_form("template.json")

        form_content = Markup(form_html)
        return await render_template("soap-notes.html", form_content=Markup(form_content))



@app.route("/create_patient", methods=["POST"])
async def create_patient():
    form = (await request.form)
    patient_name = form.get("patient-name")
    sex = form.get("sex")
    dob = form.get("dob")
    year, month, day = dob.split("-")
    year = int(year)
    month = int(month)
    day = int(day)

    print(patient_name)
    print(sex)
    print(dob)

    if not patient_name:
        return "Error: Patient name is required.", 400

    john_doe_doctor = await (db.list_all("Doctor"))
    

    new_patient = await db.add_patient(
        john_doe_doctor[0], patient_name, sex, datetime(year, month, day)
    )

    await db.add_soapnote(
        new_patient, {"skibidi": "sigma", "alpha": "wolf"}
    )

    return redirect(url_for('patient_portal'))


@app.route("/remove-patient/<patient_id>", methods=["GET", "POST"])
async def remove_patient(patient_id):
    patient = await (db.search_unique("patient", id=patient_id))
    if patient:
        print("successfully found patient to delete!")
        await (db.remove_patient(patient_id))
    else:
        print("didn't find patient id to delete!")

    
    return redirect(url_for("patient_portal"))

@app.route("/patient-portal", methods=["GET", "POST"])
async def patient_portal():
    patient_name = (await request.form).get("name-query", "")

    portal_helper = utils.PatientPortal(db)
    table_body_html = await portal_helper.get_patient_table(patient_name)

    return await render_template(
        "patient-portal.html",
        table_body=Markup(table_body_html),
    )

@app.route("/appointments", methods=["GET", "POST"])
async def appointments_index():

    if request.method == "POST":
        appointment_data = await request.get_json()
        title = appointment_data['title']
        start = appointment_data['start']
        end = appointment_data['end']
        doctor = appointment_data['doctor']
        patient = appointment_data['patient']

        print(f"New appointment: {title}, {start} - {end}, Doctor: {doctor}, Patient: {patient}")
        appointments_helper = utils.Appointments(db)

        # Format date
        try:
            start = datetime.fromisoformat(start).isoformat() + 'Z'
            end = datetime.fromisoformat(end).isoformat() + 'Z'
        except ValueError as e:
            print(f"Date formatting error: {e}")
            return jsonify({"success": False, "message": "Error in rendering date!\nError Code 32A"}), 400

        doctor_return = await appointments_helper.get_doctor_id(doctor)
        patient_return = await appointments_helper.get_patientid_by_name(patient)

        print("doctor")
        print(doctor_return)
        print("patient")
        print(patient_return)

        if doctor_return and patient_return:
            doctor_obj = doctor_return[0]
            doctor_id = doctor_return[1]

            patient_obj = patient_return[0]
            patient_id = patient_return[1]

            showMessage = "Successfully added appointment date!"
            await appointments_helper.push_appointment_date(doctor_id, patient_id, title, start, end)
            return await render_template("appointments.html")
        else:
            print("Appointments didn't go through!")
            return jsonify({"success": False, "message": "Error in finding doctor and patient!\nError Code: 32B"}), 400
    
    return await render_template("appointments.html")
    
@app.route("/appointments/doctor=<string:doctor>", methods=["GET"])
async def get_doctor_events(doctor):
    appointments_helper = utils.Appointments(db)

    doctor_return = await appointments_helper.get_doctor_id(doctor)
    doctor_id = doctor_return[1]

    events = await appointments_helper.get_events_by_doctor_id(doctor_id)

    print(events)

    if events:
        return events
    else:
        return jsonify({"success": False, "message": "No events found for this doctor."}), 404

@app.route("/appointments/patient=<string:patientID>", methods=["GET"])
async def get_patient_by_id(patientID):
    appointments_helper = utils.Appointments(db)

    print("hi")

    id_return = await appointments_helper.get_patient_name_by_id(patientID)

    print(id_return)
    
    if id_return:
        return id_return
    else:
        return None
    

# Endpoint to submits patient data
@app.post("/api/submit")
async def submit():
    # TODO: implement data push function

    form = await request.form

    test = json.dumps(form)

    print(test)

    return ""


if __name__ == "__main__":
    port_number = int(os.environ.get("PORT", 80))  # Default to 80 if PORT is not set
    app.run(debug=True, use_reloader=True, host="0.0.0.0", port=port_number)
