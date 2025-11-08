# 新しいReactコンポーネントを作成

このコマンドは、TypeScript + Reactプロジェクトで新しいコンポーネントを標準的な構造で作成します。

## 使い方

```
/new-component ComponentName
```

## 実行内容

以下の手順で新しいコンポーネントを作成してください:

1. **ディレクトリ作成**
   - `src/components/$ARGUMENTS/` ディレクトリを作成

2. **コンポーネントファイル作成** (`src/components/$ARGUMENTS/$ARGUMENTS.tsx`)
   ```typescript
   interface ${ARGUMENTS}Props {
     // TODO: Props定義
   }

   export function $ARGUMENTS({ }: ${ARGUMENTS}Props) {
     return (
       <div>
         {/* TODO: 実装 */}
       </div>
     )
   }
   ```

3. **テストファイル作成** (`src/components/$ARGUMENTS/$ARGUMENTS.test.tsx`)
   ```typescript
   import { render, screen } from '@testing-library/react'
   import { $ARGUMENTS } from './$ARGUMENTS'

   describe('$ARGUMENTS', () => {
     it('should render successfully', () => {
       render(<$ARGUMENTS />)
       // TODO: テスト実装
     })
   })
   ```

4. **エクスポートファイル作成** (`src/components/$ARGUMENTS/index.ts`)
   ```typescript
   export { $ARGUMENTS } from './$ARGUMENTS'
   export type { ${ARGUMENTS}Props } from './$ARGUMENTS'
   ```

5. **テスト実行**
   - `npm test src/components/$ARGUMENTS` を実行して動作確認

6. **完了報告**
   - 作成したファイルの一覧を表示
   - 次のステップ（Props定義、実装）を案内
