"use client";

import { useState } from "react";

const ACCESS_KEY = process.env.NEXT_PUBLIC_WEB3FORMS_ACCESS_KEY;

const FIELD =
  "mt-2 w-full rounded-sm border border-line bg-bg1 px-3 py-2.5 text-sm text-fg0 placeholder:text-fg2 transition-colors duration-[var(--dur-fast)] focus:border-accent";

export default function ContactForm({ email, cv }) {
  const [status, setStatus] = useState("idle"); // idle | sending | sent | error
  const [error, setError] = useState("");

  // Without a key configured, don't render a form that silently fails.
  if (!ACCESS_KEY) {
    return (
      <div className="rounded-md border border-line bg-bg1 p-6">
        <p className="t-body-sm text-fg1">
          Prefer email? Reach me directly at{" "}
          <a href={`mailto:${email}`} className="link text-accent">
            {email}
          </a>
          .
        </p>
      </div>
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("sending");
    setError("");

    const form = e.currentTarget;
    const data = new FormData(form);
    data.append("access_key", ACCESS_KEY);
    data.append("subject", "New message from your portfolio site");

    try {
      const res = await fetch("https://api.web3forms.com/submit", {
        method: "POST",
        body: data,
      });
      const json = await res.json();

      if (json.success) {
        setStatus("sent");
        form.reset();
      } else {
        setStatus("error");
        setError(json.message || "Something went wrong. Please try again.");
      }
    } catch {
      setStatus("error");
      setError("Network error — please check your connection and try again.");
    }
  }

  if (status === "sent") {
    return (
      <div className="rounded-md border border-line bg-bg1 p-6">
        <p className="t-h4 text-fg0">Message sent.</p>
        <p className="t-body-sm mt-2 text-fg1">
          Thanks for getting in touch — I&apos;ll reply as soon as I can.
        </p>
        <button
          type="button"
          onClick={() => setStatus("idle")}
          className="link t-body-sm mt-4 text-accent"
        >
          Send another
        </button>
      </div>
    );
  }

  const errored = status === "error";

  return (
    <form onSubmit={handleSubmit}>
      {/* honeypot — hidden from users, catches naive bots */}
      <input
        type="checkbox"
        name="botcheck"
        tabIndex={-1}
        autoComplete="off"
        className="hidden"
        aria-hidden="true"
      />

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="name" className="t-label block text-fg2">
            Name
          </label>
          <input
            id="name"
            name="name"
            type="text"
            required
            autoComplete="name"
            aria-invalid={errored || undefined}
            aria-describedby={errored ? "form-error" : undefined}
            className={FIELD}
          />
        </div>

        <div>
          <label htmlFor="email" className="t-label block text-fg2">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            aria-invalid={errored || undefined}
            aria-describedby={errored ? "form-error" : undefined}
            className={FIELD}
          />
        </div>
      </div>

      <div className="mt-5">
        <label htmlFor="message" className="t-label block text-fg2">
          Message
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          required
          aria-invalid={errored || undefined}
          aria-describedby={errored ? "form-error" : undefined}
          className={`${FIELD} resize-y`}
        />
      </div>

      {errored ? (
        <p id="form-error" role="alert" className="t-body-sm mt-4 text-accent">
          {error}
        </p>
      ) : null}

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
        <button
          type="submit"
          disabled={status === "sending"}
          className="rounded-sm bg-accent px-5 py-2.5 text-sm font-medium text-bg0 transition-colors duration-[var(--dur-fast)] hover:bg-accent-hover active:bg-accent-active disabled:cursor-default disabled:opacity-50"
        >
          {status === "sending" ? "Sending…" : "Send message"}
        </button>
        <p className="t-meta text-fg2">
          or download the{" "}
          <a
            href={cv}
            target="_blank"
            rel="noopener noreferrer"
            className="link text-fg1"
          >
            CV — PDF
          </a>
        </p>
      </div>
    </form>
  );
}
