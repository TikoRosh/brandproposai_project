let selectedProposalId = null;
let selectedBonus = 150;

function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("hidden");
  window.setTimeout(() => toast.classList.add("hidden"), 2600);
}

function showFloatingPoints(points) {
  const el = document.getElementById("floatingPoints");
  if (!el) return;
  el.textContent = `+${points} pts`;
  el.classList.remove("hidden");
  window.setTimeout(() => el.classList.add("hidden"), 1400);
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove("hidden");
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("hidden");
}

async function postJson(url, payload = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function bindModalClose() {
  document.querySelectorAll("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", () => closeModal(button.dataset.closeModal));
  });

  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (event) => {
      if (event.target === modal) modal.classList.add("hidden");
    });
  });
}

function bindGenerateProposal() {
  const button = document.querySelector("[data-generate-proposal]");
  if (!button) return;

  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "Generating...";

    try {
      const data = await postJson("/api/proposals/generate", {
        title: "AI Commercial Proposal",
        company: "New Enterprise Client",
      });
      openModal("generationModal");
      showFloatingPoints(data.points_awarded);
      showToast(`Commercial Proposal #${data.proposal_id} created!`);
      window.setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
      showToast(error.message);
    } finally {
      button.disabled = false;
      button.textContent = "🚀 Generate New Commercial Proposal";
    }
  });
}

function bindReviewModal() {
  document.querySelectorAll("[data-open-review]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedProposalId = button.dataset.id;
      selectedBonus = 150;

      document.getElementById("reviewTitle").textContent = `Review CP #${button.dataset.id}`;
      document.getElementById("reviewCompany").textContent = `${button.dataset.company} · ${button.dataset.title}`;
      document.getElementById("reviewConfidence").textContent = `${button.dataset.confidence}%`;
      document.getElementById("reviewAuthor").textContent = button.dataset.author;
      document.getElementById("reviewText").textContent = button.dataset.text;

      document.querySelectorAll(".bonus-btn").forEach((item) => {
        item.classList.toggle("active", item.dataset.bonus === "150");
      });

      openModal("reviewModal");
    });
  });

  document.querySelectorAll(".bonus-btn").forEach((button) => {
    button.addEventListener("click", () => {
      selectedBonus = Number(button.dataset.bonus);
      document.querySelectorAll(".bonus-btn").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
    });
  });

  const approveButton = document.querySelector("[data-approve-proposal]");
  if (approveButton) {
    approveButton.addEventListener("click", async () => {
      if (!selectedProposalId) return;
      approveButton.disabled = true;

      try {
        const data = await postJson(`/api/proposals/${selectedProposalId}/approve`, {
          bonus: selectedBonus,
          comment: document.getElementById("reviewComment")?.value || "",
        });
        closeModal("reviewModal");
        showFloatingPoints(data.points_awarded);
        showToast(`CP #${selectedProposalId} approved! +${data.points_awarded} pts awarded.`);
        window.setTimeout(() => window.location.reload(), 1500);
      } catch (error) {
        showToast(error.message);
      } finally {
        approveButton.disabled = false;
      }
    });
  }

  const rejectButton = document.querySelector("[data-reject-proposal]");
  if (rejectButton) {
    rejectButton.addEventListener("click", async () => {
      if (!selectedProposalId) return;
      rejectButton.disabled = true;

      try {
        await postJson(`/api/proposals/${selectedProposalId}/reject`);
        closeModal("reviewModal");
        showToast(`CP #${selectedProposalId} rejected.`);
        window.setTimeout(() => window.location.reload(), 1200);
      } catch (error) {
        showToast(error.message);
      } finally {
        rejectButton.disabled = false;
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  bindModalClose();
  bindGenerateProposal();
  bindReviewModal();
});
