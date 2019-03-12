import { NamedPage } from 'vj/misc/PageLoader';

import * as domainEnum from 'vj/constant/domain';

const page = new NamedPage('domain_manage_join_applications', () => {
  const $role = $('[name="role"]');
  const $expire = $('[name="expire"]');
  const $code = $('[name="invitation_code"]');
  const codeCharPool = "acdefghjkmnprtwxyz23478";
  let lastRandomCode;

  function generateCode() {
    let text = "";
    for (let i = 0; i < 4; i++) {
      text += codeCharPool.charAt(Math.floor(Math.random() * codeCharPool.length));
    }
    return text;
  }

  function updateFormState() {
    const method = parseInt($('[name="method"]:checked').val(), 10);
    $role.prop('disabled', method === domainEnum.JOIN_METHOD_NONE).trigger('vjFormDisableUpdate');
    $expire.prop('disabled', method === domainEnum.JOIN_METHOD_NONE).trigger('vjFormDisableUpdate');
    $code.prop('disabled', method !== domainEnum.JOIN_METHOD_CODE).trigger('vjFormDisableUpdate');
  }
  updateFormState();
  $('[name="method"]').change(() => {
    updateFormState();
    const method = parseInt($('[name="method"]:checked').val(), 10);
    if (($code.val().trim().length < 1 || $code.val().trim() === lastRandomCode) && method === domainEnum.JOIN_METHOD_CODE) {
      lastRandomCode = generateCode()
      $code.val(lastRandomCode);
    }
  });
});

export default page;
