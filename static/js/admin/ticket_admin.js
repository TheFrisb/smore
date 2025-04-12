document.addEventListener("DOMContentLoaded", function () {
  function updateAllAutocompletes(productId) {
    // Handle existing inlines
    document
      .querySelectorAll('select[id^="id_bet_lines-"][id$="-match"]')
      .forEach((matchInput) => {
        const $ = django.jQuery;
        const $select = $(matchInput);
        const baseUrl = $select.data("ajax--url");

        // Only update if this is a match field
        if (!matchInput.dataset.fieldName === "match") return;

        // Destroy existing Select2
        if ($select.data("select2")) {
          $select.select2("destroy");
          $select.removeData("select2");
        }

        // Update URL with product_id
        const url = new URL(baseUrl, window.location.origin);
        url.searchParams.set("product_id", productId || "");
        $select.data("ajax--url", url.toString());

        // Reinitialize Select2
        $select.select2({
          ajax: {
            url: url.toString(),
            dataType: "json",
            delay: 250,
            data: function (params) {
              return {
                term: params.term,
                page: params.page,
                app_label: matchInput.dataset.appLabel,
                model_name: matchInput.dataset.modelName,
                field_name: matchInput.dataset.fieldName,
                product_id: productId,
              };
            },
            processResults: function (data) {
              return {
                results: data.results,
                pagination: { more: data.more },
              };
            },
          },
          minimumInputLength: 1,
        });
      });
  }

  // Handle product change
  const productSelect = document.getElementById("id_product");
  if (productSelect) {
    productSelect.addEventListener("change", function () {
      updateAllAutocompletes(this.value);
    });

    // Initial setup with current value
    updateAllAutocompletes(productSelect.value);
  }

  // Handle new inline additions
  django.jQuery(document).on("formset:added", function (event, $row) {
    console.log($row);
    const productId = document.getElementById("id_product")?.value;
    setTimeout(() => updateAllAutocompletes(productId), 300);
  });
});
