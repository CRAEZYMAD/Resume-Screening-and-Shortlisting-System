// Load score breakdown without reloading the page
async function showDetails(id) {
  const d = await (await fetch(`/api/candidate/${id}`)).json();
  const box = document.getElementById("details");
  box.style.display = "block";
  box.innerHTML = `
    <h3></h3>
    <p><b>Overall match:</b> ${d.match_score}%</p>
    <p>Skill match (50%): ${d.skill_score}% &nbsp;|&nbsp;
       Text similarity (30%): ${d.text_similarity}% &nbsp;|&nbsp;
       Experience (20%): ${d.experience_score}%</p>
    <p><b>Education:</b> <span id="edu"></span></p>
    <p><b>Matched skills:</b> <span id="ms"></span></p>
    <p><b>Missing skills:</b> <span id="mi"></span></p>`;
  // textContent avoids injecting resume text as HTML
  box.querySelector("h3").textContent = d.name;
  document.getElementById("edu").textContent = d.education || "-";
  document.getElementById("ms").textContent = d.matched_skills || "-";
  document.getElementById("mi").textContent = d.missing_skills || "-";
  box.scrollIntoView({ behavior: "smooth" });
}
