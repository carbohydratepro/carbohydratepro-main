"use strict";
(() => {
    const visibleStepForms = (list) => Array.from(list.querySelectorAll("[data-step-form]")).filter((form) => !form.classList.contains("d-none") && form.dataset.deleted !== "true");
    const initialiseCookingForm = () => {
        var _a, _b;
        const root = document.querySelector("[data-cooking-form]");
        if (!root)
            return;
        const singleSection = root.querySelector("[data-single-recipe-section]");
        const stepSection = root.querySelector("[data-step-recipe-section]");
        const stepList = root.querySelector("[data-step-list]");
        const addButton = root.querySelector("[data-step-add]");
        const countLabel = root.querySelector("[data-step-count]");
        const totalForms = root.querySelector('[name="steps-TOTAL_FORMS"]');
        const emptyTemplate = root.querySelector("[data-empty-step-template]");
        const maxSteps = Number((_a = root.dataset.maxSteps) !== null && _a !== void 0 ? _a : "10");
        if (!singleSection || !stepSection || !stepList || !addButton || !countLabel || !totalForms || !emptyTemplate)
            return;
        const updateStepState = () => {
            const forms = visibleStepForms(stepList);
            forms.forEach((form, index) => {
                const number = form.querySelector("[data-step-number]");
                const position = form.querySelector('input[name$="-position"]');
                const up = form.querySelector("[data-step-up]");
                const down = form.querySelector("[data-step-down]");
                if (number)
                    number.textContent = String(index + 1);
                if (position)
                    position.value = String(index + 1);
                if (up)
                    up.disabled = index === 0;
                if (down)
                    down.disabled = index === forms.length - 1;
            });
            countLabel.textContent = String(forms.length);
            addButton.disabled = forms.length >= maxSteps;
        };
        const bindStepForm = (stepForm) => {
            var _a, _b, _c;
            if (stepForm.dataset.stepBound === "true")
                return;
            stepForm.dataset.stepBound = "true";
            (_a = stepForm.querySelector("[data-step-remove]")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", () => {
                const deleteInput = stepForm.querySelector('input[name$="-DELETE"]');
                if (deleteInput)
                    deleteInput.checked = true;
                stepForm.dataset.deleted = "true";
                stepForm.classList.add("d-none");
                updateStepState();
            });
            (_b = stepForm.querySelector("[data-step-up]")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", () => {
                const previous = visibleStepForms(stepList)[visibleStepForms(stepList).indexOf(stepForm) - 1];
                if (previous)
                    stepList.insertBefore(stepForm, previous);
                updateStepState();
            });
            (_c = stepForm.querySelector("[data-step-down]")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", () => {
                const forms = visibleStepForms(stepList);
                const next = forms[forms.indexOf(stepForm) + 1];
                if (next)
                    stepList.insertBefore(next, stepForm);
                updateStepState();
            });
            bindImagePreviews(stepForm);
        };
        const addStep = () => {
            var _a, _b;
            const hiddenExisting = Array.from(stepList.querySelectorAll("[data-step-form].d-none")).find((form) => form.dataset.deleted !== "true");
            if (hiddenExisting) {
                hiddenExisting.classList.remove("d-none");
                bindStepForm(hiddenExisting);
                updateStepState();
                (_a = hiddenExisting.querySelector("textarea")) === null || _a === void 0 ? void 0 : _a.focus();
                return;
            }
            if (visibleStepForms(stepList).length >= maxSteps)
                return;
            const formIndex = Number(totalForms.value);
            const html = emptyTemplate.innerHTML.split("__prefix__").join(String(formIndex));
            const wrapper = document.createElement("div");
            wrapper.innerHTML = html.trim();
            const newForm = wrapper.firstElementChild;
            if (!newForm)
                return;
            stepList.appendChild(newForm);
            totalForms.value = String(formIndex + 1);
            bindStepForm(newForm);
            updateStepState();
            (_b = newForm.querySelector("textarea")) === null || _b === void 0 ? void 0 : _b.focus();
        };
        const selectedMode = () => { var _a, _b; return (_b = (_a = root.querySelector('input[name="recipe_mode"]:checked')) === null || _a === void 0 ? void 0 : _a.value) !== null && _b !== void 0 ? _b : "single"; };
        const updateRecipeMode = () => {
            const isSteps = selectedMode() === "steps";
            singleSection.classList.toggle("d-none", isSteps);
            stepSection.classList.toggle("d-none", !isSteps);
            if (isSteps && visibleStepForms(stepList).length === 0)
                addStep();
        };
        root.querySelectorAll('input[name="recipe_mode"]').forEach((radio) => {
            radio.addEventListener("change", updateRecipeMode);
        });
        stepList.querySelectorAll("[data-step-form]").forEach(bindStepForm);
        addButton.addEventListener("click", addStep);
        (_b = root.querySelector("form")) === null || _b === void 0 ? void 0 : _b.addEventListener("submit", updateStepState);
        bindImagePreviews(root);
        updateStepState();
        updateRecipeMode();
    };
    function bindImagePreviews(scope) {
        scope.querySelectorAll(".cooking-photo-input").forEach((input) => {
            if (input.dataset.previewBound === "true")
                return;
            input.dataset.previewBound = "true";
            input.addEventListener("change", () => {
                var _a, _b;
                const preview = (_a = input.closest(".cooking-file-field")) === null || _a === void 0 ? void 0 : _a.querySelector(".cooking-file-preview");
                if (!preview)
                    return;
                preview.replaceChildren();
                const file = (_b = input.files) === null || _b === void 0 ? void 0 : _b[0];
                if (!file)
                    return;
                const image = document.createElement("img");
                image.alt = "選択した写真のプレビュー";
                image.src = URL.createObjectURL(file);
                image.addEventListener("load", () => URL.revokeObjectURL(image.src), { once: true });
                preview.appendChild(image);
            });
        });
    }
    const initialiseRecipeBook = () => {
        const book = document.querySelector("[data-recipe-book]");
        if (!book)
            return;
        const pages = Array.from(book.querySelectorAll("[data-recipe-page]"));
        const previous = book.querySelector("[data-recipe-prev]");
        const next = book.querySelector("[data-recipe-next]");
        const indicator = book.querySelector("[data-recipe-indicator]");
        let currentIndex = 0;
        let touchStartX = null;
        const showPage = (index) => {
            currentIndex = Math.max(0, Math.min(index, pages.length - 1));
            pages.forEach((page, pageIndex) => page.classList.toggle("d-none", pageIndex !== currentIndex));
            if (previous)
                previous.disabled = currentIndex === 0;
            if (next)
                next.disabled = currentIndex === pages.length - 1;
            if (indicator)
                indicator.textContent = `${currentIndex + 1} / ${pages.length}`;
        };
        previous === null || previous === void 0 ? void 0 : previous.addEventListener("click", () => showPage(currentIndex - 1));
        next === null || next === void 0 ? void 0 : next.addEventListener("click", () => showPage(currentIndex + 1));
        book.addEventListener("touchstart", (event) => {
            var _a, _b;
            touchStartX = (_b = (_a = event.changedTouches[0]) === null || _a === void 0 ? void 0 : _a.clientX) !== null && _b !== void 0 ? _b : null;
        }, { passive: true });
        book.addEventListener("touchend", (event) => {
            var _a, _b;
            if (touchStartX === null)
                return;
            const endX = (_b = (_a = event.changedTouches[0]) === null || _a === void 0 ? void 0 : _a.clientX) !== null && _b !== void 0 ? _b : touchStartX;
            const distance = endX - touchStartX;
            if (Math.abs(distance) >= 50)
                showPage(currentIndex + (distance < 0 ? 1 : -1));
            touchStartX = null;
        }, { passive: true });
        showPage(0);
    };
    document.addEventListener("DOMContentLoaded", () => {
        initialiseCookingForm();
        initialiseRecipeBook();
    });
})();
