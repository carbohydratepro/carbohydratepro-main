((): void => {
  const visibleStepForms = (list: HTMLElement): HTMLElement[] =>
    Array.from(list.querySelectorAll<HTMLElement>("[data-step-form]")).filter(
      (form) => !form.classList.contains("d-none") && form.dataset.deleted !== "true",
    );

  const initialiseCookingForm = (): void => {
    const root = document.querySelector<HTMLElement>("[data-cooking-form]");
    if (!root) return;

    const singleSection = root.querySelector<HTMLElement>("[data-single-recipe-section]");
    const stepSection = root.querySelector<HTMLElement>("[data-step-recipe-section]");
    const stepList = root.querySelector<HTMLElement>("[data-step-list]");
    const addButton = root.querySelector<HTMLButtonElement>("[data-step-add]");
    const countLabel = root.querySelector<HTMLElement>("[data-step-count]");
    const totalForms = root.querySelector<HTMLInputElement>('[name="steps-TOTAL_FORMS"]');
    const emptyTemplate = root.querySelector<HTMLTemplateElement>("[data-empty-step-template]");
    const maxSteps = Number(root.dataset.maxSteps ?? "10");
    if (!singleSection || !stepSection || !stepList || !addButton || !countLabel || !totalForms || !emptyTemplate) return;

    const updateStepState = (): void => {
      const forms = visibleStepForms(stepList);
      forms.forEach((form, index) => {
        const number = form.querySelector<HTMLElement>("[data-step-number]");
        const position = form.querySelector<HTMLInputElement>('input[name$="-position"]');
        const up = form.querySelector<HTMLButtonElement>("[data-step-up]");
        const down = form.querySelector<HTMLButtonElement>("[data-step-down]");
        if (number) number.textContent = String(index + 1);
        if (position) position.value = String(index + 1);
        if (up) up.disabled = index === 0;
        if (down) down.disabled = index === forms.length - 1;
      });
      countLabel.textContent = String(forms.length);
      addButton.disabled = forms.length >= maxSteps;
    };

    const bindStepForm = (stepForm: HTMLElement): void => {
      if (stepForm.dataset.stepBound === "true") return;
      stepForm.dataset.stepBound = "true";
      stepForm.querySelector<HTMLButtonElement>("[data-step-remove]")?.addEventListener("click", () => {
        const deleteInput = stepForm.querySelector<HTMLInputElement>('input[name$="-DELETE"]');
        if (deleteInput) deleteInput.checked = true;
        stepForm.dataset.deleted = "true";
        stepForm.classList.add("d-none");
        updateStepState();
      });
      stepForm.querySelector<HTMLButtonElement>("[data-step-up]")?.addEventListener("click", () => {
        const previous = visibleStepForms(stepList)[visibleStepForms(stepList).indexOf(stepForm) - 1];
        if (previous) stepList.insertBefore(stepForm, previous);
        updateStepState();
      });
      stepForm.querySelector<HTMLButtonElement>("[data-step-down]")?.addEventListener("click", () => {
        const forms = visibleStepForms(stepList);
        const next = forms[forms.indexOf(stepForm) + 1];
        if (next) stepList.insertBefore(next, stepForm);
        updateStepState();
      });
      bindImagePreviews(stepForm);
    };

    const addStep = (): void => {
      const hiddenExisting = Array.from(stepList.querySelectorAll<HTMLElement>("[data-step-form].d-none")).find(
        (form) => form.dataset.deleted !== "true",
      );
      if (hiddenExisting) {
        hiddenExisting.classList.remove("d-none");
        bindStepForm(hiddenExisting);
        updateStepState();
        hiddenExisting.querySelector<HTMLTextAreaElement>("textarea")?.focus();
        return;
      }
      if (visibleStepForms(stepList).length >= maxSteps) return;
      const formIndex = Number(totalForms.value);
      const html = emptyTemplate.innerHTML.split("__prefix__").join(String(formIndex));
      const wrapper = document.createElement("div");
      wrapper.innerHTML = html.trim();
      const newForm = wrapper.firstElementChild as HTMLElement | null;
      if (!newForm) return;
      stepList.appendChild(newForm);
      totalForms.value = String(formIndex + 1);
      bindStepForm(newForm);
      updateStepState();
      newForm.querySelector<HTMLTextAreaElement>("textarea")?.focus();
    };

    const selectedMode = (): string =>
      root.querySelector<HTMLInputElement>('input[name="recipe_mode"]:checked')?.value ?? "single";
    const updateRecipeMode = (): void => {
      const isSteps = selectedMode() === "steps";
      singleSection.classList.toggle("d-none", isSteps);
      stepSection.classList.toggle("d-none", !isSteps);
      if (isSteps && visibleStepForms(stepList).length === 0) addStep();
    };

    root.querySelectorAll<HTMLInputElement>('input[name="recipe_mode"]').forEach((radio) => {
      radio.addEventListener("change", updateRecipeMode);
    });
    stepList.querySelectorAll<HTMLElement>("[data-step-form]").forEach(bindStepForm);
    addButton.addEventListener("click", addStep);
    root.querySelector<HTMLFormElement>("form")?.addEventListener("submit", updateStepState);
    bindImagePreviews(root);
    updateStepState();
    updateRecipeMode();
  };

  function bindImagePreviews(scope: ParentNode): void {
    scope.querySelectorAll<HTMLInputElement>(".cooking-photo-input").forEach((input) => {
      if (input.dataset.previewBound === "true") return;
      input.dataset.previewBound = "true";
      input.addEventListener("change", () => {
        const preview = input.closest<HTMLElement>(".cooking-file-field")?.querySelector<HTMLElement>(".cooking-file-preview");
        if (!preview) return;
        preview.replaceChildren();
        const file = input.files?.[0];
        if (!file) return;
        const image = document.createElement("img");
        image.alt = "選択した写真のプレビュー";
        image.src = URL.createObjectURL(file);
        image.addEventListener("load", () => URL.revokeObjectURL(image.src), { once: true });
        preview.appendChild(image);
      });
    });
  }

  const initialiseRecipeBook = (): void => {
    const book = document.querySelector<HTMLElement>("[data-recipe-book]");
    if (!book) return;
    const pages = Array.from(book.querySelectorAll<HTMLElement>("[data-recipe-page]"));
    const previous = book.querySelector<HTMLButtonElement>("[data-recipe-prev]");
    const next = book.querySelector<HTMLButtonElement>("[data-recipe-next]");
    const indicator = book.querySelector<HTMLElement>("[data-recipe-indicator]");
    let currentIndex = 0;
    let touchStartX: number | null = null;

    const showPage = (index: number): void => {
      currentIndex = Math.max(0, Math.min(index, pages.length - 1));
      pages.forEach((page, pageIndex) => page.classList.toggle("d-none", pageIndex !== currentIndex));
      if (previous) previous.disabled = currentIndex === 0;
      if (next) next.disabled = currentIndex === pages.length - 1;
      if (indicator) indicator.textContent = `${currentIndex + 1} / ${pages.length}`;
    };

    previous?.addEventListener("click", () => showPage(currentIndex - 1));
    next?.addEventListener("click", () => showPage(currentIndex + 1));
    book.addEventListener("touchstart", (event: TouchEvent) => {
      touchStartX = event.changedTouches[0]?.clientX ?? null;
    }, { passive: true });
    book.addEventListener("touchend", (event: TouchEvent) => {
      if (touchStartX === null) return;
      const endX = event.changedTouches[0]?.clientX ?? touchStartX;
      const distance = endX - touchStartX;
      if (Math.abs(distance) >= 50) showPage(currentIndex + (distance < 0 ? 1 : -1));
      touchStartX = null;
    }, { passive: true });
    showPage(0);
  };

  document.addEventListener("DOMContentLoaded", () => {
    initialiseCookingForm();
    initialiseRecipeBook();
  });
})();
