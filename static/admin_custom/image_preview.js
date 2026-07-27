(function () {
  function getPreviewElements(input) {
    const targetId = input.dataset.previewTarget;
    if (!targetId) {
      return null;
    }

    const preview = document.getElementById(targetId);
    if (!preview) {
      return null;
    }

    return {
      preview,
      link: preview.querySelector(".admin-image-preview-link"),
      image: preview.querySelector(".admin-image-preview-image"),
      placeholder: preview.querySelector(".admin-image-preview-placeholder"),
    };
  }

  function togglePreviewState(elements, hasImage) {
    elements.preview.classList.toggle("is-empty", !hasImage);
    elements.link.classList.toggle("is-hidden", !hasImage);
    elements.image.classList.toggle("is-hidden", !hasImage);
    elements.placeholder.classList.toggle("is-hidden", hasImage);
  }

  function applyPreview(elements, imageUrl, altText) {
    const hasImage = Boolean(imageUrl);
    togglePreviewState(elements, hasImage);

    if (!hasImage) {
      elements.link.removeAttribute("href");
      elements.image.removeAttribute("src");
      elements.image.alt = "";
      return;
    }

    elements.link.href = imageUrl;
    elements.image.src = imageUrl;
    elements.image.alt = altText || "";
  }

  function restorePreview(input) {
    const elements = getPreviewElements(input);
    if (!elements) {
      return;
    }

    applyPreview(elements, elements.preview.dataset.originalUrl || "", "");
  }

  function updatePreview(input) {
    const elements = getPreviewElements(input);
    if (!elements) {
      return;
    }

    const file = input.files && input.files[0];
    if (!file) {
      restorePreview(input);
      return;
    }

    const looksLikeImage =
      (file.type && file.type.indexOf("image/") === 0) ||
      /\.(png|jpe?g|webp|gif|svg|ico)$/i.test(file.name);

    if (!looksLikeImage) {
      restorePreview(input);
      return;
    }

    const reader = new FileReader();
    reader.addEventListener("load", function (event) {
      applyPreview(elements, event.target && event.target.result ? event.target.result : "", file.name);
    });
    reader.readAsDataURL(file);
  }

  function handleClearCheckbox(checkbox) {
    const fieldName = checkbox.name.replace(/-clear$/, "");
    const input = document.querySelector('input[type="file"][name="' + fieldName + '"]');
    if (!input) {
      return;
    }

    if (checkbox.checked) {
      const elements = getPreviewElements(input);
      if (!elements) {
        return;
      }
      applyPreview(elements, "", "");
      return;
    }

    updatePreview(input);
  }

  document.addEventListener("change", function (event) {
    const target = event.target;

    if (target.matches('input[type="file"][data-preview-target]')) {
      updatePreview(target);
      return;
    }

    if (target.matches('input[type="checkbox"][name$="-clear"]')) {
      handleClearCheckbox(target);
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[type="file"][data-preview-target]').forEach(function (input) {
      restorePreview(input);
    });
  });
})();
