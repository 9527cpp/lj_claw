import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:8000/api/models/';

test('1. Settings page model editing test', async ({ page }) => {
  // First, verify API update works directly
  const directUpdate = await page.request.put('http://localhost:8000/api/models/minimax', {
    headers: { 'Content-Type': 'application/json' },
    data: {
      id: 'minimax',
      name: 'Test Model Updated',
      provider: 'minimax',
      api_key: '',
      api_base: '',
      enabled: true
    }
  });
  expect(directUpdate.ok()).toBeTruthy();
  const directJson = await directUpdate.json();
  expect(directJson.success).toBe(true);

  // Refresh the page and verify UI reflects the change
  await page.goto(`${BASE_URL}/settings`);
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('.model-card', { timeout: 10000 });

  // Check that the model name is displayed as updated
  const modelName = await page.locator('.model-card h3').first().textContent();
  await page.screenshot({ path: '/Users/lijun/workspace/lj_claw/frontend/e2e/test1-edit-success.png' });
  expect(modelName).toBe('Test Model Updated');

  // Restore original name via API
  const restoreUpdate = await page.request.put('http://localhost:8000/api/models/minimax', {
    headers: { 'Content-Type': 'application/json' },
    data: {
      id: 'minimax',
      name: 'MiniMax',
      provider: 'minimax',
      api_key: '',
      api_base: '',
      enabled: true
    }
  });
  expect(restoreUpdate.ok()).toBeTruthy();
});

test('2. Settings page model deletion test', async ({ page }) => {
  // First, add a test model via API
  const addModel = await page.request.post('http://localhost:8000/api/models/', {
    headers: { 'Content-Type': 'application/json' },
    data: {
      id: 'test-model',
      name: '测试模型',
      provider: 'openai',
      api_key: 'sk-test123456789',
      api_base: 'https://api.openai.com/v1',
      enabled: true
    }
  });
  expect(addModel.ok()).toBeTruthy();

  // Refresh page and verify model appears
  await page.goto(`${BASE_URL}/settings`);
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('.model-card', { timeout: 10000 });

  // Verify model is displayed
  const bodyText = await page.textContent('body');
  await page.screenshot({ path: '/Users/lijun/workspace/lj_claw/frontend/e2e/test2-delete-added.png' });
  expect(bodyText).toContain('测试模型');

  // Find and click delete button for the test model
  page.on('dialog', dialog => dialog.accept());
  const deleteButton = page.locator('.model-card:has-text("测试模型") button:has-text("删除")');
  await deleteButton.click();

  // Wait for page to update
  await page.waitForTimeout(2000);

  // Verify model was deleted via API
  const afterDeleteModels = await page.request.get(API_URL);
  const afterDeleteData = await afterDeleteModels.json();
  const deletedModel = afterDeleteData.models?.find((m: any) => m.id === 'test-model');

  await page.screenshot({ path: '/Users/lijun/workspace/lj_claw/frontend/e2e/test2-delete-result.png' });
  expect(deletedModel).toBeUndefined();
});

test('3. Settings page model activation test', async ({ page }) => {
  await page.goto(`${BASE_URL}/settings`);
  await page.waitForLoadState('networkidle');

  // Wait for models to load
  await page.waitForSelector('.model-card', { timeout: 10000 });

  // Find activate buttons (Chinese: 激活)
  const activateButtons = page.locator('button:has-text("激活")');
  const count = await activateButtons.count();

  if (count > 0) {
    // Click activate on first available model
    await activateButtons.first().click();
    await page.waitForTimeout(1500);

    // Verify "使用中" (In Use) badge appears
    const badge = page.locator('.active-badge');
    const badgeCount = await badge.count();
    expect(badgeCount).toBeGreaterThan(0);
  } else {
    console.log('Only one model available, skipping activation test');
  }

  await page.screenshot({ path: '/Users/lijun/workspace/lj_claw/frontend/e2e/test3-activate-result.png' });
});

test('4. API path verification - PUT without trailing slash', async ({ page }) => {
  // Test PUT without trailing slash
  const response = await page.request.put('http://localhost:8000/api/models/minimax', {
    headers: { 'Content-Type': 'application/json' },
    data: {
      id: 'minimax',
      name: 'Verification-Test',
      provider: 'anthropic',
      api_key: 'test',
      api_base: 'https://test.com',
      enabled: true
    }
  });

  expect(response.status()).toBe(200);
  const json = await response.json();
  expect(json.success).toBe(true);

  // Restore original value
  const restoreResponse = await page.request.put('http://localhost:8000/api/models/minimax', {
    headers: { 'Content-Type': 'application/json' },
    data: {
      id: 'minimax',
      name: 'MiniMax',
      provider: 'minimax',
      api_key: '',
      api_base: '',
      enabled: true
    }
  });

  expect(restoreResponse.status()).toBe(200);
  const restoreJson = await restoreResponse.json();
  expect(restoreJson.success).toBe(true);
});
