const API="http://localhost:8000";

async function start(){
 let r=await fetch(API+"/start"); let d=await r.json();
 showQ(d.question);
}

async function submitA(){
 let ans=document.getElementById("answer").value;
 let exp=document.getElementById("explanation").value;

 let r=await fetch(API+"/answer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({student_answer:ans,explanation:exp})});
 let d=await r.json();

 if(d.finished){ showSummary(d.summary); }
 else{ showQ(d.next_question); }
}

function showQ(q){
 document.getElementById("app").innerHTML=`
 <h2>${q.question}</h2>
 <textarea id="answer"></textarea>
 <textarea id="explanation"></textarea>
 <button onclick="submitA()">Submit</button>`;
}

function showSummary(s){
 document.getElementById("app").innerHTML=`<h2>Done</h2>
 <p>Score: ${s.final_score.toFixed(2)}</p>`;
}

start();