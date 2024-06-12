import pageStyles from "../../../styles/page.module.css";

export default async function ParticipantsSurveyReportPage() {
  const res = await fetch("/api/survey/");
  //const res = await fetch("http://localhost:3003/api/get-participants-survey");
  //const res = await fetch("https://jsonplaceholder.typicode.com/posts"); //TODO:used for testing
  //const res = await fetch("../../../api/get-participants-survey");

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary.
    throw new Error(`Failed to fetch participants survey data`);
  }

  const participantsSurveyData = await res.json();
  console.log("participantsSurveyData: ", participantsSurveyData);

  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row`}>
            <div>Survey Participant's Report</div>
          </div>
          <div className={`row`}>
            <div>
              <ul>
                {participantsSurveyData.map((data) => (
                  <li key={data._id}>{data.code}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
