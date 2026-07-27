(function () {
  'use strict';

  document.documentElement.classList.add('reveal-ready');

  var body = document.body;
  var header = document.querySelector('.site-header');
  var menu = document.getElementById('mobile-menu');
  var menuOverlay = document.getElementById('menu-overlay');
  var menuToggle = document.querySelector('.menu-toggle');
  var closeMenuButton = document.querySelector('.close-menu');
  var backdrop = document.getElementById('modal-backdrop');
  var requestModal = document.getElementById('request-modal');
  var policyModal = document.getElementById('policy-modal');
  var requestForm = document.getElementById('request-form');
  var formSuccess = document.getElementById('form-success');
  var toast = document.getElementById('toast');
  var lastTrigger = null;
  var activeModal = null;
  var toastTimer = null;
  var defaultSuccessTitle = formSuccess ? formSuccess.querySelector('h3').textContent : '';
  var defaultSuccessText = formSuccess ? formSuccess.querySelector('p').textContent : '';

  function setHeaderState() {
    if (!header) return;
    header.classList.toggle('scrolled', window.scrollY > 12);
  }

  function showToast(message) {
    if (!toast) return;
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add('show');
    toastTimer = window.setTimeout(function () {
      toast.classList.remove('show');
    }, 4200);
  }

  function lockBody() {
    body.classList.add('no-scroll');
  }

  function unlockBody() {
    if ((!menu || !menu.classList.contains('is-open')) && !activeModal) {
      body.classList.remove('no-scroll');
    }
  }

  function openMenu() {
    if (!menu || !menuOverlay || activeModal) return;
    menuOverlay.hidden = false;
    menu.setAttribute('aria-hidden', 'false');
    menuToggle.setAttribute('aria-expanded', 'true');
    lockBody();
    window.requestAnimationFrame(function () {
      menuOverlay.classList.add('is-open');
      menu.classList.add('is-open');
      if (closeMenuButton) closeMenuButton.focus();
    });
  }

  function closeMenu(focusToggle) {
    if (!menu || !menu.classList.contains('is-open')) return;
    menuOverlay.classList.remove('is-open');
    menu.classList.remove('is-open');
    menu.setAttribute('aria-hidden', 'true');
    menuToggle.setAttribute('aria-expanded', 'false');
    window.setTimeout(function () {
      if (!menu.classList.contains('is-open')) menuOverlay.hidden = true;
    }, 320);
    unlockBody();
    if (focusToggle && menuToggle) menuToggle.focus();
  }

  function openModal(modal, trigger) {
    if (!modal || !backdrop) return;
    closeMenu(false);
    lastTrigger = trigger || document.activeElement;
    activeModal = modal;
    backdrop.hidden = false;
    modal.hidden = false;
    lockBody();
    window.requestAnimationFrame(function () {
      backdrop.classList.add('is-open');
      modal.classList.add('is-open');
      var autofocusTarget = modal.querySelector('input, select, textarea, button');
      if (autofocusTarget) autofocusTarget.focus();
    });
  }

  function closeModal(restoreFocus) {
    if (!activeModal || !backdrop) return;
    var modal = activeModal;
    modal.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    activeModal = null;
    window.setTimeout(function () {
      if (!modal.classList.contains('is-open')) modal.hidden = true;
      if (!activeModal) backdrop.hidden = true;
    }, 240);
    unlockBody();
    if (restoreFocus && lastTrigger && typeof lastTrigger.focus === 'function') lastTrigger.focus();
  }

  function cleanPhone(value) {
    return value.replace(/\D/g, '');
  }

  function getCsrfToken(form) {
    if (!form) return '';
    var tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return tokenInput ? tokenInput.value : '';
  }

  function getFormEndpoint(form) {
    if (!form) return window.location.pathname;
    return form.getAttribute('data-application-endpoint') || form.action || window.location.pathname;
  }

  function parseJsonResponse(response) {
    return response.text().then(function (text) {
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch (error) {
        return {};
      }
    });
  }

  function getFirstErrorMessage(items) {
    if (!items) return '';
    if (typeof items === 'string') return items;
    if (!Array.isArray(items) || !items.length) return '';
    if (typeof items[0] === 'string') return items[0];
    return items[0] && items[0].message ? items[0].message : '';
  }

  function normalizeServerErrors(payload) {
    if (!payload || typeof payload !== 'object') return {};
    if (payload.errors && typeof payload.errors === 'object') return payload.errors;
    if (!payload.error_details || typeof payload.error_details !== 'object') return {};

    var normalized = {};
    Object.keys(payload.error_details).forEach(function (fieldName) {
      normalized[fieldName] = (payload.error_details[fieldName] || [])
        .map(function (item) {
          return item && item.message ? item.message : '';
        })
        .filter(Boolean);
    });
    return normalized;
  }

  function setFieldError(fieldName, message) {
    if (!requestForm) return;
    var input = requestForm.elements[fieldName];
    var field = input ? input.closest('.field') : null;
    var error = requestForm.querySelector('[data-error-for="' + fieldName + '"]');
    if (field) field.classList.toggle('is-invalid', Boolean(message));
    if (input && message) input.setAttribute('aria-invalid', 'true');
    if (input && !message) input.removeAttribute('aria-invalid');
    if (error) error.textContent = message || '';
  }

  function clearErrors() {
    if (!requestForm) return;
    Array.prototype.forEach.call(requestForm.querySelectorAll('.field'), function (field) {
      field.classList.remove('is-invalid');
    });
    Array.prototype.forEach.call(requestForm.querySelectorAll('.field-error'), function (error) {
      error.textContent = '';
    });
  }

  function validateField(name) {
    if (!requestForm) return true;
    var element = requestForm.elements[name];
    if (!element) return true;
    var value = String(element.value || '').trim();
    var message = '';

    if (name === 'name' && value.length < 2) message = 'Укажите имя не короче 2 символов.';
    if (name === 'phone' && cleanPhone(value).length < 11) message = 'Введите телефон в понятном формате.';
    if (name === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) message = 'Введите корректный email.';
    if (name === 'service' && !value) message = 'Выберите интересующую услугу.';
    if (name === 'file') {
      var file = requestForm.elements.file.files[0];
      if (file && file.size > 2 * 1024 * 1024) message = 'Для демо-версии доступен файл до 2 МБ.';
    }

    setFieldError(name, message);
    return !message;
  }

  function applyServerErrors(errors) {
    clearErrors();
    Object.keys(errors || {}).forEach(function (name) {
      if (name === '__all__' || name === 'non_field_errors') return;
      var message = getFirstErrorMessage(errors[name]);
      if (message) setFieldError(name, message);
    });
  }

  function formatPhone(event) {
    var digits = cleanPhone(event.target.value);
    if (!digits) return;
    if (digits.charAt(0) === '8') digits = '7' + digits.slice(1);
    if (digits.charAt(0) !== '7') digits = '7' + digits;
    var result = '+7';
    if (digits.length > 1) result += ' (' + digits.slice(1, 4);
    if (digits.length >= 5) result += ') ' + digits.slice(4, 7);
    if (digits.length >= 8) result += '-' + digits.slice(7, 9);
    if (digits.length >= 10) result += '-' + digits.slice(9, 11);
    event.target.value = result;
  }

  function updateFileLabel() {
    if (!requestForm) return;
    var file = requestForm.elements.file.files[0];
    var label = document.getElementById('file-name');
    if (label) label.textContent = file ? file.name : 'Файл не выбран';
    validateField('file');
  }

  function resetFormState() {
    if (!requestForm) return;
    requestForm.reset();
    if (requestForm.elements.service_name) requestForm.elements.service_name.value = '';
    var label = document.getElementById('file-name');
    if (label) label.textContent = 'Файл не выбран';
    clearErrors();
    if (formSuccess) {
      formSuccess.hidden = true;
      var title = formSuccess.querySelector('h3');
      var text = formSuccess.querySelector('p');
      if (title) title.textContent = defaultSuccessTitle;
      if (text) text.textContent = defaultSuccessText;
    }
    requestForm.hidden = false;
  }

  function setFormTargetFromButton(button) {
    if (!requestForm) return;
    var serviceId = button.getAttribute('data-service-id');
    var serviceLabel = button.getAttribute('data-service-label');
    if (requestForm.elements.service_name) {
      requestForm.elements.service_name.value = serviceId === 'other' ? (serviceLabel || '') : '';
    }
    if (requestForm.elements.service) {
      if (serviceId && serviceId !== 'other') {
        requestForm.elements.service.value = serviceId;
      } else if (serviceId === 'other') {
        requestForm.elements.service.value = 'other';
      }
    }
  }

  function handleFormSubmit(event) {
    event.preventDefault();
    if (!requestForm) return;

    var valid = ['name', 'phone', 'email', 'service', 'file'].every(validateField);
    if (!valid) {
      var invalid = requestForm.querySelector('[aria-invalid="true"]');
      if (invalid) invalid.focus();
      showToast('Проверьте поля, отмеченные красным.');
      return;
    }

    var submitButton = requestForm.querySelector('[type="submit"]');
    var submitHtml = submitButton ? submitButton.innerHTML : '';
    var formData = new FormData(requestForm);

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Отправляем…';
    }

    fetch(getFormEndpoint(requestForm), {
      method: 'POST',
      body: formData,
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': getCsrfToken(requestForm),
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(function (response) {
        return parseJsonResponse(response).then(function (data) {
          return { response: response, data: data };
        });
      })
      .then(function (payload) {
        var response = payload.response;
        var data = payload.data || {};
        var isSuccess = typeof data.ok === 'boolean' ? data.ok : Boolean(data.success);
        if (!response.ok || !isSuccess) {
          var errors = normalizeServerErrors(data);
          if (Object.keys(errors).length) applyServerErrors(errors);
          data.message = getFirstErrorMessage(errors.non_field_errors) || getFirstErrorMessage(errors.__all__) || data.message;
          showToast(data.message || 'Не удалось отправить заявку.');
          throw new Error('submit_failed');
        }

        if (formSuccess) {
          var successTitle = formSuccess.querySelector('h3');
          var successText = formSuccess.querySelector('p');
          if (successTitle && data.title) successTitle.textContent = data.title;
          if (successText && data.message) successText.textContent = data.message;
          requestForm.hidden = true;
          formSuccess.hidden = false;
        }
        requestForm.reset();
        if (requestForm.elements.service_name) requestForm.elements.service_name.value = '';
        var label = document.getElementById('file-name');
        if (label) label.textContent = 'Файл не выбран';
        showToast(data.message || 'Заявка отправлена.');
      })
      .catch(function (error) {
        if (error && error.message === 'submit_failed') return;
        showToast('Не удалось отправить заявку. Попробуйте еще раз.');
      })
      .finally(function () {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.innerHTML = submitHtml || 'Отправить заявку <span class="button-arrow" aria-hidden="true">↗</span>';
        }
      });
  }

  function setupReveal() {
    var items = document.querySelectorAll('.reveal');
    var staggeredParents = ['service-grid', 'product-list', 'advantage-grid', 'steps-list'];

    Array.prototype.forEach.call(items, function (item) {
      var parent = item.parentElement;
      var revealIndex = 0;
      var child;

      if (!parent || staggeredParents.indexOf(parent.className) === -1) return;

      child = parent.firstElementChild;
      while (child && child !== item) {
        if (child.classList.contains('reveal')) revealIndex += 1;
        child = child.nextElementSibling;
      }

      item.style.setProperty('--reveal-delay', Math.min(revealIndex * 55, 275) + 'ms');
    });

    if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      Array.prototype.forEach.call(items, function (item) { item.classList.add('visible'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.1 });

    Array.prototype.forEach.call(items, function (item) { observer.observe(item); });
  }

  function setupParallax() {
    var area = document.querySelector('[data-parallax-area]');
    if (!area || !window.matchMedia('(pointer: fine)').matches || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var cards = area.querySelectorAll('[data-parallax]');
    area.addEventListener('pointermove', function (event) {
      var rect = area.getBoundingClientRect();
      var x = (event.clientX - rect.left) / rect.width - 0.5;
      var y = (event.clientY - rect.top) / rect.height - 0.5;
      Array.prototype.forEach.call(cards, function (card) {
        var amount = Number(card.getAttribute('data-parallax'));
        card.style.translate = (x * amount) + 'px ' + (y * amount) + 'px';
      });
    });
    area.addEventListener('pointerleave', function () {
      Array.prototype.forEach.call(cards, function (card) { card.style.translate = ''; });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    setHeaderState();
    setupReveal();
    setupParallax();

    var currentYear = document.getElementById('current-year');
    if (currentYear) currentYear.textContent = new Date().getFullYear();

    window.addEventListener('scroll', setHeaderState, { passive: true });

    if (menuToggle) menuToggle.addEventListener('click', openMenu);
    if (closeMenuButton) closeMenuButton.addEventListener('click', function () { closeMenu(true); });
    if (menuOverlay) menuOverlay.addEventListener('click', function () { closeMenu(true); });

    Array.prototype.forEach.call(document.querySelectorAll('.mobile-nav a'), function (link) {
      link.addEventListener('click', function () { closeMenu(false); });
    });

    Array.prototype.forEach.call(document.querySelectorAll('[data-open-form]'), function (button) {
      button.addEventListener('click', function () {
        if (!requestForm) return;
        resetFormState();
        setFormTargetFromButton(button);
        openModal(requestModal, button);
      });
    });

    Array.prototype.forEach.call(document.querySelectorAll('[data-open-policy]'), function (button) {
      button.addEventListener('click', function () { openModal(policyModal, button); });
    });

    Array.prototype.forEach.call(document.querySelectorAll('.close-modal, [data-close-modal]'), function (button) {
      button.addEventListener('click', function () { closeModal(true); });
    });

    if (backdrop) backdrop.addEventListener('click', function () { closeModal(true); });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        if (activeModal) closeModal(true);
        else closeMenu(true);
      }
    });

    if (requestForm) {
      requestForm.addEventListener('submit', handleFormSubmit);
      if (requestForm.elements.phone) requestForm.elements.phone.addEventListener('input', formatPhone);
      if (requestForm.elements.service) {
        requestForm.elements.service.addEventListener('change', function () {
          if (this.value !== 'other' && requestForm.elements.service_name) {
            requestForm.elements.service_name.value = '';
          }
        });
      }
      ['name', 'phone', 'email', 'service'].forEach(function (name) {
        var eventName = name === 'service' ? 'change' : 'blur';
        if (requestForm.elements[name]) {
          requestForm.elements[name].addEventListener(eventName, function () { validateField(name); });
        }
      });
      if (requestForm.elements.file) requestForm.elements.file.addEventListener('change', updateFileLabel);
    }

    var toTopButton = document.querySelector('[data-to-top]');
    if (toTopButton) {
      toTopButton.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  });
}());
