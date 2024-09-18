import "bootstrap/dist/css/bootstrap.css";
//import styles from "./page.module.css";

import ParticipantsSurveyForm from "../app/forms/participants-survey/page.js";
//import DelegatesSurveyForm from "../app/forms/delegates-survey/page.js";

export default function HomePage() {
  return (
    <>
      <main>
        <ParticipantsSurveyForm />
        {/*<DelegatesSurveyForm />*/}
      </main>
    </>
  );
}
