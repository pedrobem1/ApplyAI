export default function Home() {
  return (
    <main className="shell">
      <section className="workspace">
        <div className="toolbar">
          <div>
            <p className="eyebrow">MVP workspace</p>
            <h1>Job Application Intelligence</h1>
          </div>
          <span className="status">Planning scaffold</span>
        </div>

        <div className="grid">
          <section className="panel">
            <h2>Resume</h2>
            <p>Upload endpoint ready for the PDF parsing pipeline.</p>
            <button type="button">Upload PDF</button>
          </section>

          <section className="panel">
            <h2>Job</h2>
            <p>URL and manual description endpoints are ready for extraction.</p>
            <input placeholder="https://company.com/jobs/software-engineering-intern" />
            <button type="button">Import URL</button>
          </section>

          <section className="panel wide">
            <h2>Analysis</h2>
            <div className="score">--%</div>
            <p>The matching pipeline will fill this view with requirements, evidence and gaps.</p>
          </section>
        </div>
      </section>
    </main>
  );
}

