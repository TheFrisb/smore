document.addEventListener("DOMContentLoaded", function () {
  function updateAutocomplete() {
    const productId = document.getElementById("id_product")?.value;
    const matchInput = document.querySelector("select[name='match']");

    if (!matchInput) return;

    const $ = django.jQuery;
    const $select = $(matchInput);
    const baseUrl = $select.data("ajax--url");

    // Destroy existing Select2 instance completely
    if ($select.data("select2")) {
      $select.select2("destroy");
      $select.removeData("select2");
    }

    // Create new URL with current product_id
    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set("product_id", productId || "");

    // Reinitialize with explicit configuration
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
  }

  const productSelect = document.getElementById("id_product");
  productSelect?.addEventListener("change", updateAutocomplete);
  updateAutocomplete(); // Initial setup
});
