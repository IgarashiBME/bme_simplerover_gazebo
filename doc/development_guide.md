# 開発ガイド

このドキュメントは本リポジトリの開発に関するガイドラインです。

## プロジェクト概要

ROS 2 Jazzy + Gazebo Harmonic で動作する4輪スキッドステアローバーのシミュレーション環境です。

## ビルド・実行

```bash
# ビルド（ワークスペースルートから）
cd ~/ros2_ws
colcon build --packages-select bme_simplerover_gazebo
source install/setup.bash

# シミュレーション起動
ros2 launch bme_simplerover_gazebo sim.launch.py

# キーボード操作（別ターミナル、対話式ターミナルが必要）
source ~/ros2_ws/install/setup.bash
ros2 run bme_simplerover_gazebo teleop_key_node.py
```

## リント・テスト

```bash
# パッケージテスト実行（ament_lint_auto + ament_lint_common）
cd ~/ros2_ws
colcon test --packages-select bme_simplerover_gazebo
colcon test-result --verbose
```

## アーキテクチャ

**シミュレーションパイプライン:** Xacro → robot_state_publisher → Gazeboスポーン → ros_gz_bridge → fake_gnss_node

launchファイル（`launch/sim.launch.py`）は以下の順序で起動します:
1. `urdf/rover.urdf.xacro` をロボットデスクリプションに変換
2. `worlds/empty.sdf` でGazeboを起動
3. robot_state_publisherでTFを配信（use_sim_time=true）
4. Gazebo内にローバーをz=0.1mの高さでスポーン
5. `config/bridge.yaml` に基づきros_gz_bridgeでトピック変換を開始
6. `fake_gnss_node` でグラウンドトゥルース位置をUTM/GnssSolutionとして配信

**ロボットモデル**（`urdf/rover.urdf.xacro`）: `base_footprint` → `base_link` → 4輪リンクで構成されるスキッドステアローバー。3つのGazeboプラグインを含む:
- `DiffDrive`: `/cmd_vel` のTwistを車輪コマンドに変換（左ペア + 右ペア）。車輪ベースのオドメトリを `odom` トピックで配信。
- `OdometryPublisher`: 物理エンジンの姿勢から直接グラウンドトゥルースオドメトリを `ground_truth_odom` で配信（車輪スリップ誤差なし）。
- `JointStatePublisher`: 車輪のジョイント状態を配信。

**トピックブリッジ**（`config/bridge.yaml`）: ROS 2とGazebo間のメッセージ型マッピング:
- `/cmd_vel`（ROS→GZ）: 速度コマンド
- `/odom`（GZ→ROS）: 車輪ベースのオドメトリ（旋回時にスリップ誤差あり）
- `/ground_truth/odom`（GZ→ROS）: 物理エンジンのグラウンドトゥルースオドメトリ
- `/tf`, `/joint_states`（GZ→ROS）: 座標変換とジョイント状態

**スクリプト**（`scripts/`）:
- `fake_gnss_node.py`: `/ground_truth/odom` を購読し、`bme_common_msgs/GnssSolution` を `/gnss/solution` でUTM座標として配信。UTM原点はパラメータで設定可能。
- `teleop_key_node.py`: キーボード操作（w/a/s/d/q/e）。キー入力がない場合はゼロ速度を配信。launchファイルには含まれず単独で起動。

## 主要な規約

- ビルドシステム: ament_cmake
- ロボットパラメータ（寸法、質量、摩擦）は `rover.urdf.xacro` 先頭のxacroプロパティで定義
- シミュレーション全体で `use_sim_time:=true` を使用
- オドメトリフレーム: `odom` → `base_footprint`（30 Hz）
- ヘディングはREP-103準拠: ENU規約（東=0°、北=90°、反時計回り正）、範囲 -180°〜180°

## Gazebo摩擦に関する注意事項

- 各ホイールに `<fdir1>1 0 0</fdir1>` を指定し、`mu1`/`mu2` をホイールのローカルフレームに固定する必要がある。これがないと摩擦方向がワールド座標に依存し、ロボットの向きによって旋回挙動が変化する。
- `mu1`（転がり方向）: 牽引力のため高い値を設定。`mu2`（横方向）: スキッドステア旋回を可能にするため低い値を設定。
- `mu2` の値を調整することでその場旋回のしやすさを制御できる。

## ターミナルrawモード（teleopノード）

- `teleop_key_node.py` は `tty.setcbreak()` でターミナルのエコーを無効化する。`atexit.register()` で終了時のターミナル復元を保証すること。
- キー切替時の遅延を防ぐため、各tickでstdinバッファを完全にdrain（`while select(...)` ループ）すること。
