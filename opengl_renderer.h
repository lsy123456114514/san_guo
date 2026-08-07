#pragma once

#ifdef _WIN32
    #ifdef RENDERER_EXPORTS
        #define RENDERER_API __declspec(dllexport)
    #else
        #define RENDERER_API __declspec(dllimport)
    #endif
#else
    #define RENDERER_API
#endif

#include <cstdint>

struct Color4f {
    float r, g, b, a;
};

struct Vec3f {
    float x, y, z;
};

struct ProjectileData {
    float x, y, z;
    int type;
    float rotation;
};

struct PickupData {
    float x, z;
    float bob_offset;
    float rotation;
    int item_type;
    float r, g, b, a;
};

struct TechBlockData {
    float x, z;
    int tech_type;
    int active;
    float rotation;
    float r, g, b, a;
};

struct LocationData {
    float x, z;
    int type;
    float height;
    float r, g, b;
    int owner;
    float scale;
};

struct NPCData {
    float x, z;
    const char* name;
    float r, g, b;
    int selected;
    float animation_offset;
};

struct EnemyData {
    float x, z;
    int type;
    float health;
    float max_health;
    float r, g, b;
};

struct GeneralData {
    float x, z;
    const char* name;
    float r, g, b;
    int has_weapon;
    float animation_offset;
};

struct PetData {
    float x, z;
    int type;
    float r, g, b;
    float animation_offset;
};

struct PlayerData {
    float x, y, z;
    float r, g, b;
    float yaw;
};

struct FollowerData {
    float x, z;
    const char* name;
    float r, g, b;
    float animation_offset;
};

struct TreeData {
    float x, z;
    float scale;
};

struct StructureData {
    float x, z;
    const char* name;
    float size;
    float height;
    float r, g, b;
};

extern "C" RENDERER_API void init_renderer(int screen_width, int screen_height);
extern "C" RENDERER_API void cleanup_renderer();

extern "C" RENDERER_API void render_terrain(
    float player_x, float player_y, float player_z,
    float visible_range,
    float block_size,
    float height
);

extern "C" RENDERER_API void render_projectiles(
    ProjectileData* projectiles,
    int count
);

extern "C" RENDERER_API void render_pickups(
    PickupData* pickups,
    int count
);

extern "C" RENDERER_API void render_tech_block(const TechBlockData* block);

extern "C" RENDERER_API void render_tree(const TreeData* tree);

extern "C" RENDERER_API void render_trees(
    TreeData* trees,
    int count
);

extern "C" RENDERER_API void render_large_structure(const StructureData* structure);

extern "C" RENDERER_API void render_structures(
    StructureData* structures,
    int count
);

extern "C" RENDERER_API void render_location(const LocationData* location);

extern "C" RENDERER_API void render_locations(
    LocationData* locations,
    int count
);

extern "C" RENDERER_API void render_npc(const NPCData* npc);

extern "C" RENDERER_API void render_npcs(
    NPCData* npcs,
    int count
);

extern "C" RENDERER_API void render_enemy(const EnemyData* enemy);

extern "C" RENDERER_API void render_enemies(
    EnemyData* enemies,
    int count
);

extern "C" RENDERER_API void render_general(const GeneralData* general);

extern "C" RENDERER_API void render_generals(
    GeneralData* generals,
    int count
);

extern "C" RENDERER_API void render_pet(const PetData* pet);

extern "C" RENDERER_API void render_pets(
    PetData* pets,
    int count
);

extern "C" RENDERER_API void render_player(const PlayerData* player);

extern "C" RENDERER_API void render_follower(const FollowerData* follower);

extern "C" RENDERER_API void render_followers(
    FollowerData* followers,
    int count
);

extern "C" RENDERER_API void render_particles(
    Vec3f* positions,
    Color4f* colors,
    int count
);

extern "C" RENDERER_API const char* get_renderer_error();